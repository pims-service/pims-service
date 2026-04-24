from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction, IntegrityError
from django.utils import timezone
from .models import Activity, Submission
from .serializers import ActivitySerializer, DailySubmissionSerializer, SubmissionSerializer
from users.permissions import BaselineCompleted
from django.contrib.auth import get_user_model

User = get_user_model()

class DailyActivityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling daily participant activities and submissions.
    """
    serializer_class = ActivitySerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Activity.objects.none()
        return Activity.objects.filter(group=user.group)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """
        Returns the current activity for the user based on their group.
        """
        user = request.user
        activity = Activity.objects.filter(group=user.group).first()
        if not activity:
            return Response({"detail": "No activity found for your group."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(activity)
        
        # Check if already submitted today
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        submitted_today = Submission.objects.filter(
            user=user,
            submission_date__gte=today_start
        ).exists()
        
        data = serializer.data
        data['submitted_today'] = submitted_today
        return Response(data)

    @action(detail=False, methods=['post'])
    def submit(self, request):
        """
        Submits the content for the user's daily activity.
        Uses database-level locking to prevent duplicate submissions during high load.
        """
        user = request.user
        
        # High-concurrency optimization: 
        # Use an atomic transaction and lock the user record during the check-and-create phase.
        with transaction.atomic():
            # Lock the user row to prevent race conditions from simultaneous requests
            User.objects.select_for_update().get(pk=user.user_id)
            
            # Re-check the submission state inside the lock
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if Submission.objects.filter(user=user, submission_date__gte=today_start).exists():
                return Response(
                    {"detail": "Activity already submitted for today."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Proceed with submission
            serializer = DailySubmissionSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                current_day = user.current_experiment_day
                try:
                    serializer.save(user=user, experiment_day=current_day)
                except IntegrityError:
                    return Response(
                        {"detail": "You have already submitted this specific activity."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Update Redis cache to reflect submission
                from django.core.cache import cache
                cache_key = f"user_{user.user_id}_submitted_{timezone.now().date()}"
                now = timezone.now()
                tomorrow = (now + timezone.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                timeout = int((tomorrow - now).total_seconds())
                if timeout > 0:
                    cache.set(cache_key, True, timeout=timeout)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Standard ViewSet for listing activities.
    """
    permission_classes = [BaselineCompleted]
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

class SubmissionViewSet(viewsets.ModelViewSet):
    """
    Standard ViewSet for handling task submissions.
    """
    permission_classes = [BaselineCompleted]
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
