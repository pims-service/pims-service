from rest_framework import generics, permissions
from .models import Activity, Submission
from .serializers import ActivitySerializer, SubmissionSerializer
from phases.models import Phase
from django.utils import timezone
from users.permissions import BaselineCompleted

class ActivityListView(generics.ListAPIView):
    serializer_class = ActivitySerializer
    permission_classes = (permissions.IsAuthenticated, BaselineCompleted,)

    def get_queryset(self):
        today = timezone.now().date()
        current_phase = Phase.objects.filter(start_date__lte=today, end_date__gte=today).first()
        if current_phase:
            return Activity.objects.filter(assigned_phase=current_phase)
        return Activity.objects.none()

class SubmissionCreateView(generics.CreateAPIView):
    serializer_class = SubmissionSerializer
    permission_classes = (permissions.IsAuthenticated, BaselineCompleted,)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserSubmissionListView(generics.ListAPIView):
    serializer_class = SubmissionSerializer
    permission_classes = (permissions.IsAuthenticated, BaselineCompleted,)

    def get_queryset(self):
        return Submission.objects.filter(user=self.request.user)
