from rest_framework import generics, permissions, status, pagination
from rest_framework.response import Response as DRFResponse
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
    queryset = Questionnaire.objects.filter(is_active=True)
    serializer_class = QuestionnaireSerializer
    permission_classes = (permissions.IsAuthenticated,)

class QuestionnaireDetailView(generics.RetrieveAPIView):
    queryset = Questionnaire.objects.all()
    serializer_class = QuestionnaireSerializer
    permission_classes = (permissions.IsAuthenticated,)

class ResponseSetListCreateView(generics.ListCreateAPIView):
    serializer_class = ResponseSetSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        # Users see their own response sets, ordered by most recent completion
        return ResponseSet.objects.filter(user=self.request.user).select_related('questionnaire').order_by('-completed_at')

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
            
        # If they already completed it (not just draft), block it based on assessment type logic
        try:
            q_obj = Questionnaire.objects.get(id=questionnaire_id)
            if q_obj.assessment_type == 'SOCIODEMOGRAPHIC' and user.has_completed_sociodemographic:
                raise ValidationError({"detail": "You have already completed the sociodemographic assessment."})
            if q_obj.is_posttest:
                if milestone in [None, '7_DAYS']:
                    if not user.is_posttest_due:
                        raise ValidationError({"detail": "Post-test is not available yet. Complete 7 days first."})
                    if user.has_completed_posttest:
                        raise ValidationError({"detail": "You have already completed the post-test."})
                elif milestone in ['3_MONTHS', '6_MONTHS', '1_YEAR']:
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
        return super().get_queryset().filter(user=self.request.user, status='DRAFT')

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
        ).select_related('user', 'questionnaire').order_by('-completed_at')

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
        ).select_related('user', 'questionnaire').prefetch_related(
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
        ).select_related('user', 'questionnaire').order_by('-completed_at')


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
        ).select_related('user', 'questionnaire').order_by('-completed_at')


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
        ).select_related('user', 'questionnaire').prefetch_related(
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
        ).select_related('user', 'questionnaire').order_by('-completed_at')


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
        ).select_related('user', 'questionnaire').prefetch_related(
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
        ).select_related('user', 'questionnaire').order_by('-completed_at')


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
        ).select_related('user', 'questionnaire').prefetch_related(
            'responses__question',
            'responses__selected_option'
        )


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
