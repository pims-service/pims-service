from rest_framework import generics, permissions, status
from rest_framework.response import Response as DRFResponse
# Researcher Data Views
from .models import Questionnaire, ResponseSet, Response
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

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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
