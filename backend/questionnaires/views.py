from rest_framework import generics, permissions, status, pagination
from rest_framework.response import Response as DRFResponse
from rest_framework.views import APIView
# Researcher Data Views
from .models import Questionnaire, ResponseSet, Response

class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return DRFResponse({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'results': data
        })
from .serializers import (
    QuestionnaireSerializer, 
    ResponseSetSerializer, 
    AdminResponseSetSerializer,
    ResponseSetSubmitSerializer
)

class QuestionnaireListView(generics.ListAPIView):
    queryset = Questionnaire.objects.filter(is_active=True).prefetch_related('questions__options')
    serializer_class = QuestionnaireSerializer
    permission_classes = (permissions.IsAuthenticated,)

class QuestionnaireDetailView(generics.RetrieveAPIView):
    queryset = Questionnaire.objects.all().prefetch_related('questions__options')
    serializer_class = QuestionnaireSerializer
    permission_classes = (permissions.IsAuthenticated,)

class ResponseSetListCreateView(generics.ListCreateAPIView):
    serializer_class = ResponseSetSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        # Users see their own response sets, ordered by most recent completion
        return ResponseSet.objects.filter(user=self.request.user).select_related('questionnaire').prefetch_related('responses__selected_option').order_by('-completed_at')

    def create(self, request, *args, **kwargs):
        from rest_framework.exceptions import ValidationError
        from .serializers import ResponseSetSerializer
        
        questionnaire_id = request.data.get('questionnaire')
        milestone = request.data.get('milestone')
        user = self.request.user
        
        # Check for existing DRAFT response set for this user/questionnaire/milestone
        existing_set = ResponseSet.objects.filter(
            user=user, 
            questionnaire_id=questionnaire_id,
            milestone=milestone,
            status='DRAFT'
        ).first()
        
        if existing_set:
            serializer = self.get_serializer(existing_set)
            return DRFResponse(serializer.data, status=status.HTTP_200_OK)

        # Check if they have already completed this assessment
        if ResponseSet.objects.filter(
            user=user,
            questionnaire_id=questionnaire_id,
            milestone=milestone
        ).exists():
            raise ValidationError({"detail": "You have already completed this assessment."})
            
        # If they already completed it (not just draft), block it based on assessment type logic
        try:
            q_obj = Questionnaire.objects.get(id=questionnaire_id)
            if q_obj.assessment_type == 'SOCIODEMOGRAPHIC' and user.has_completed_sociodemographic:
                raise ValidationError({"detail": "You have already completed the sociodemographic assessment."})
            if q_obj.is_posttest or (q_obj.assessment_type == 'PSYCHOMETRIC' and milestone != 'SIGNUP'):
                if milestone in [None, '7_DAYS']:
                    if not user.is_posttest_due:
                        raise ValidationError({"detail": "Post-test is not available yet. Complete 7 days first."})
                    if user.has_completed_posttest:
                        raise ValidationError({"detail": "You have already completed the post-test."})
                elif milestone in ['1_MONTH', '3_MONTHS', '6_MONTHS', '1_YEAR']:
                    if not user.has_completed_posttest:
                        raise ValidationError({"detail": "You must complete the 7-day post-test first."})
                    if user.get_due_milestone != milestone:
                        if ResponseSet.objects.filter(user=user, status='COMPLETED', milestone=milestone).exists():
                            raise ValidationError({"detail": f"You have already completed the {milestone} assessment."})
                        else:
                            raise ValidationError({"detail": f"The {milestone} assessment is not available yet."})
        except Questionnaire.DoesNotExist:
            pass

        from django.db import IntegrityError
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            # Handle race condition from React StrictMode double-posting
            existing_set = ResponseSet.objects.filter(
                user=user, 
                questionnaire_id=questionnaire_id,
                status='DRAFT'
            ).first()
            if existing_set:
                serializer = self.get_serializer(existing_set)
                return DRFResponse(serializer.data, status=status.HTTP_200_OK)
            raise

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ResponseSetDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single response set with full questionnaire context (questions + options).
    Used by the Results page to render the post-assessment feedback.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return ResponseSet.objects.filter(
            user=self.request.user
        ).select_related('questionnaire').prefetch_related(
            'questionnaire__questions__options',
            'responses__selected_option'
        )

    def get_serializer_class(self):
        from .serializers import ResponseSetDetailSerializer
        return ResponseSetDetailSerializer


class ResponseSetSubmitView(generics.UpdateAPIView):
    """
    Endpoint to submit all responses and mark the set as COMPLETED.
    """
    queryset = ResponseSet.objects.all()
    serializer_class = ResponseSetSubmitSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ['post', 'put', 'patch']

    def get_queryset(self):
        # Users can only submit their own response sets
        return super().get_queryset().filter(user=self.request.user, status__in=['DRAFT', 'COMPLETED'])

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if instance.status == 'COMPLETED':
            serializer = self.get_serializer(instance)
            return DRFResponse(serializer.data, status=status.HTTP_200_OK)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return DRFResponse(serializer.data)

    def post(self, request, *args, **kwargs):
        # Alias POST to perform the update
        return self.update(request, *args, **kwargs)

class ResponseSetSaveDraftView(generics.UpdateAPIView):
    """
    Endpoint to save draft responses without completing the set.
    """
    queryset = ResponseSet.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ['post', 'put', 'patch']

    def get_serializer_class(self):
        from .serializers import ResponseSetDraftSerializer
        return ResponseSetDraftSerializer

    def get_queryset(self):
        # Users can only modify their own DRAFT response sets
        return super().get_queryset().filter(user=self.request.user, status='DRAFT')

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

class ResponseSetOptInView(generics.UpdateAPIView):
    """
    Endpoint to update the opt-in status for safety protocol.
    """
    queryset = ResponseSet.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ['post', 'put', 'patch']

    def get_queryset(self):
        # Users can only update their own response sets
        return super().get_queryset().filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        response_set = self.get_object()
        opt_in = request.data.get('opt_in', False)
        response_set.suicide_risk_opt_in = opt_in
        response_set.save(update_fields=['suicide_risk_opt_in'])

        from .tasks import refresh_suicide_risk_admin_cache_task
        refresh_suicide_risk_admin_cache_task.delay()

        return DRFResponse({'status': 'opt-in updated', 'suicide_risk_opt_in': response_set.suicide_risk_opt_in})

class AdminT0ResponseListView(generics.ListAPIView):
    """
    Researcher-only view to list all completed T0 baseline psychometric assessments.
    """
    serializer_class = AdminResponseSetSerializer
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return ResponseSet.objects.filter(
            milestone='SIGNUP',
            questionnaire__assessment_type='PSYCHOMETRIC',
            status='COMPLETED'
        ).select_related('user__group', 'questionnaire').prefetch_related(
            'responses__question',
            'responses__selected_option'
        ).order_by('-completed_at')

class AdminT0ResponseDetailView(generics.RetrieveAPIView):
    """
    Researcher-only view to inspect a specific T0 baseline psychometric submission.
    """
    serializer_class = AdminResponseSetSerializer
    permission_classes = (permissions.IsAdminUser,)

    def get_queryset(self):
        return ResponseSet.objects.filter(
            milestone='SIGNUP',
            questionnaire__assessment_type='PSYCHOMETRIC',
            status='COMPLETED'
        ).select_related('user__group', 'questionnaire').prefetch_related(
            'responses__question',
            'responses__selected_option'
        )


class AdminT1ResponseListView(generics.ListAPIView):
    """
    Researcher-only view to list all completed T1 follow-up (Day 7) psychometric assessments.
    """
    serializer_class = AdminResponseSetSerializer
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return ResponseSet.objects.filter(
            milestone='7_DAYS',
            questionnaire__assessment_type='PSYCHOMETRIC',
            status='COMPLETED'
        ).select_related('user__group', 'questionnaire').prefetch_related(
            'responses__question',
            'responses__selected_option'
        ).order_by('-completed_at')


class AdminT1ResponseDetailView(generics.RetrieveAPIView):
    """
    Researcher-only view to inspect a specific T1 follow-up (Day 7) psychometric submission.
    """
    serializer_class = AdminResponseSetSerializer
    permission_classes = (permissions.IsAdminUser,)

    def get_queryset(self):
        return ResponseSet.objects.filter(
            milestone='7_DAYS',
            questionnaire__assessment_type='PSYCHOMETRIC',
            status='COMPLETED'
        ).select_related('user__group', 'questionnaire').prefetch_related(
            'responses__question',
            'responses__selected_option'
        )


class AdminTFirstMonthResponseListView(generics.ListAPIView):
    """
    Researcher-only view to list all completed T-First-Month follow-up (Day 30) psychometric assessments.
    """
    serializer_class = AdminResponseSetSerializer
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return ResponseSet.objects.filter(
            milestone='1_MONTH',
            questionnaire__assessment_type='PSYCHOMETRIC',
            status='COMPLETED'
        ).select_related('user', 'questionnaire').order_by('-completed_at')


class AdminTFirstMonthResponseDetailView(generics.RetrieveAPIView):
    """
    Researcher-only view to inspect a specific T-First-Month follow-up (Day 30) psychometric submission.
    """
    serializer_class = AdminResponseSetSerializer
    permission_classes = (permissions.IsAdminUser,)

    def get_queryset(self):
        return ResponseSet.objects.filter(
            milestone='1_MONTH',
            questionnaire__assessment_type='PSYCHOMETRIC',
            status='COMPLETED'
        ).select_related('user', 'questionnaire').prefetch_related(
            'responses__question',
            'responses__selected_option'
        )


class AdminT2ResponseListView(generics.ListAPIView):
    """
    Researcher-only view to list all completed T2 follow-up (Day 90) psychometric assessments.
    """
    serializer_class = AdminResponseSetSerializer
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return ResponseSet.objects.filter(
            milestone='3_MONTHS',
            questionnaire__assessment_type='PSYCHOMETRIC',
            status='COMPLETED'
        ).select_related('user__group', 'questionnaire').prefetch_related(
            'responses__question',
            'responses__selected_option'
        ).order_by('-completed_at')


class AdminT2ResponseDetailView(generics.RetrieveAPIView):
    """
    Researcher-only view to inspect a specific T2 follow-up (Day 90) psychometric submission.
    """
    serializer_class = AdminResponseSetSerializer
    permission_classes = (permissions.IsAdminUser,)

    def get_queryset(self):
        return ResponseSet.objects.filter(
            milestone='3_MONTHS',
            questionnaire__assessment_type='PSYCHOMETRIC',
            status='COMPLETED'
        ).select_related('user__group', 'questionnaire').prefetch_related(
            'responses__question',
            'responses__selected_option'
        )


class AdminT3ResponseListView(generics.ListAPIView):
    """
    Researcher-only view to list all completed T3 follow-up (Month 6) psychometric assessments.
    """
    serializer_class = AdminResponseSetSerializer
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return ResponseSet.objects.filter(
            milestone='6_MONTHS',
            questionnaire__assessment_type='PSYCHOMETRIC',
            status='COMPLETED'
        ).select_related('user__group', 'questionnaire').prefetch_related(
            'responses__question',
            'responses__selected_option'
        ).order_by('-completed_at')


class AdminT3ResponseDetailView(generics.RetrieveAPIView):
    """
    Researcher-only view to inspect a specific T3 follow-up (Month 6) psychometric submission.
    """
    serializer_class = AdminResponseSetSerializer
    permission_classes = (permissions.IsAdminUser,)

    def get_queryset(self):
        return ResponseSet.objects.filter(
            milestone='6_MONTHS',
            questionnaire__assessment_type='PSYCHOMETRIC',
            status='COMPLETED'
        ).select_related('user__group', 'questionnaire').prefetch_related(
            'responses__question',
            'responses__selected_option'
        )


class AdminT4ResponseListView(generics.ListAPIView):
    """
    Researcher-only view to list all completed T4 follow-up (Month 12) psychometric assessments.
    """
    serializer_class = AdminResponseSetSerializer
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return ResponseSet.objects.filter(
            milestone='1_YEAR',
            questionnaire__assessment_type='PSYCHOMETRIC',
            status='COMPLETED'
        ).select_related('user__group', 'questionnaire').prefetch_related(
            'responses__question',
            'responses__selected_option'
        ).order_by('-completed_at')


class AdminT4ResponseDetailView(generics.RetrieveAPIView):
    """
    Researcher-only view to inspect a specific T4 follow-up (Month 12) psychometric submission.
    """
    serializer_class = AdminResponseSetSerializer
    permission_classes = (permissions.IsAdminUser,)

    def get_queryset(self):
        return ResponseSet.objects.filter(
            milestone='1_YEAR',
            questionnaire__assessment_type='PSYCHOMETRIC',
            status='COMPLETED'
        ).select_related('user__group', 'questionnaire').prefetch_related(
            'responses__question',
            'responses__selected_option'
        )


class AdminSuicideRiskFollowUpsView(APIView):
    """
    Admin dashboard data for suicide-risk flagged participants.
    Served from Redis cache, refreshed automatically on opt-in/risk events and daily via Celery.
    """
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        from .safety_cache import get_suicide_risk_admin_cache

        show = request.query_params.get("show", "opt_in")
        status_filter = request.query_params.get("status", "PENDING").upper()

        payload = get_suicide_risk_admin_cache(refresh_if_missing=True)
        if not payload:
            return DRFResponse(
                {
                    "last_refreshed_at": None,
                    "total_flagged": 0,
                    "opt_in_count": 0,
                    "count": 0,
                    "next": False,
                    "previous": False,
                    "cases": [],
                },
                status=status.HTTP_200_OK,
            )

        if show == "all":
            cases = payload["cases"]
        else:
            cases = payload["opt_in_cases"]

        # Filter by status
        cases = [c for c in cases if c.get("suicide_risk_status", "PENDING").upper() == status_filter]

        # Manual Pagination
        page_size = 10
        try:
            page = int(request.query_params.get("page", 1))
        except ValueError:
            page = 1

        total_cases = len(cases)
        start = (page - 1) * page_size
        end = start + page_size

        paginated_cases = cases[start:end]
        has_next = end < total_cases
        has_previous = start > 0

        return DRFResponse(
            {
                "last_refreshed_at": payload["last_refreshed_at"],
                "total_flagged": payload["total_flagged"],
                "opt_in_count": payload["opt_in_count"],
                "count": total_cases,
                "next": has_next,
                "previous": has_previous,
                "cases": paginated_cases,
            },
            status=status.HTTP_200_OK,
        )


class AdminSuicideRiskFollowUpDetailView(APIView):
    """
    Update endpoint for suicide risk cases.
    """
    permission_classes = (permissions.IsAdminUser,)

    def patch(self, request, pk):
        try:
            response_set = ResponseSet.objects.get(id=pk, suicide_risk_triggered=True)
        except ResponseSet.DoesNotExist:
            return DRFResponse({"detail": "Case not found."}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get("suicide_risk_status")
        if not new_status:
            return DRFResponse({"detail": "suicide_risk_status field is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        new_status = new_status.upper()
        if new_status not in ["PENDING", "RESOLVED"]:
            return DRFResponse({"detail": "Invalid status value. Choose PENDING or RESOLVED."}, status=status.HTTP_400_BAD_REQUEST)

        response_set.suicide_risk_status = new_status
        response_set.save(update_fields=["suicide_risk_status"])

        # Force refresh of cache
        from .safety_cache import refresh_suicide_risk_admin_cache
        refresh_suicide_risk_admin_cache()

        return DRFResponse({
            "response_set_id": str(response_set.id),
            "suicide_risk_status": response_set.suicide_risk_status
        }, status=status.HTTP_200_OK)


class DueMilestoneView(generics.GenericAPIView):
    """
    Endpoint to retrieve the user's currently due longitudinal assessment milestone.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        return DRFResponse({
            'due_milestone': user.get_due_milestone
        }, status=status.HTTP_200_OK)
