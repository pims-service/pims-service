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
        user = self.request.user
        
        # Check for existing DRAFT response set for this user/questionnaire
        existing_set = ResponseSet.objects.filter(
            user=user, 
            questionnaire_id=questionnaire_id,
            status='DRAFT'
        ).first()
        
        if existing_set:
            serializer = self.get_serializer(existing_set)
            return DRFResponse(serializer.data, status=status.HTTP_200_OK)
            
        # If it's a baseline and they already completed it (not just draft), block it
        try:
            q_obj = Questionnaire.objects.get(id=questionnaire_id)
            if q_obj.is_baseline and user.has_completed_baseline:
                raise ValidationError({"detail": "You have already completed the baseline assessment."})
            if q_obj.is_posttest:
                if not user.is_posttest_due:
                    raise ValidationError({"detail": "Post-test is not available yet. Complete 7 days first."})
                if user.has_completed_posttest:
                    raise ValidationError({"detail": "You have already completed the post-test."})
        except Questionnaire.DoesNotExist:
            pass

        return super().create(request, *args, **kwargs)

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

class AdminBaselineResponseListView(generics.ListAPIView):
    """
    Researcher-only view to list all completed baseline assessments.
    """
    serializer_class = AdminResponseSetSerializer
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return ResponseSet.objects.filter(
            questionnaire__is_baseline=True,
            status='COMPLETED'
        ).select_related('user', 'questionnaire').order_by('-completed_at')

class AdminBaselineResponseDetailView(generics.RetrieveAPIView):
    """
    Researcher-only view to inspect a specific baseline submission.
    """
    serializer_class = AdminResponseSetSerializer
    permission_classes = (permissions.IsAdminUser,)

    def get_queryset(self):
        return ResponseSet.objects.filter(
            status='COMPLETED'
        ).select_related('user', 'questionnaire').prefetch_related(
            'responses__question',
            'responses__selected_option'
        )

class AdminPosttestResponseListView(generics.ListAPIView):
    """
    Researcher-only view to list all completed Day 7 post-test assessments.
    """
    serializer_class = AdminResponseSetSerializer
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return ResponseSet.objects.filter(
            questionnaire__is_posttest=True,
            status='COMPLETED'
        ).select_related('user', 'questionnaire').order_by('-completed_at')

class AdminPosttestResponseDetailView(generics.RetrieveAPIView):
    """
    Researcher-only view to inspect a specific post-test submission.
    """
    serializer_class = AdminResponseSetSerializer
    permission_classes = (permissions.IsAdminUser,)

    def get_queryset(self):
        return ResponseSet.objects.filter(
            questionnaire__is_posttest=True,
            status='COMPLETED'
        ).select_related('user', 'questionnaire').prefetch_related(
            'responses__question',
            'responses__selected_option'
        )
