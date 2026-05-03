from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.core.cache import cache
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
        from django.db.models import Q
        return Activity.objects.filter(Q(group=user.group) | Q(group__isnull=True))

    @action(detail=False, methods=['get'])
    def current(self, request):
        """
        Returns the current activity for the user based on their group and individual timeline.
        Uses Redis to cache the current day and submission status for maximum performance.
        """
        user = request.user
        current_day = user.current_experiment_day

        if not current_day:
            return Response({"detail": "Baseline not completed."}, status=status.HTTP_404_NOT_FOUND)
        
        if current_day > 7:
            return Response({"detail": "Trial period completed."}, status=status.HTTP_200_OK)

        from django.db.models import Q
        activity = Activity.objects.filter(Q(group=user.group) | Q(group__isnull=True), day_number=current_day).first()
        if not activity:
            return Response({"detail": f"No activity found for your group on Day {current_day}."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(activity)
        
        # Check if already submitted today using Redis caching
        cache_key = f"user_{user.user_id}_submitted_{timezone.now().date()}"
        submitted_today = cache.get(cache_key)
        
        if submitted_today is None:
            # Fallback to DB and populate cache
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            submitted_today = Submission.objects.filter(
                user=user,
                submission_date__gte=today_start
            ).exists()
            # Cache until end of day
            now = timezone.now()
            tomorrow = (now + timezone.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            timeout = int((tomorrow - now).total_seconds())
            if timeout > 0:
                cache.set(cache_key, submitted_today, timeout=timeout)
        
        data = serializer.data
        data['submitted_today'] = submitted_today
        data['current_day'] = current_day
        
        if submitted_today:
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            submission = Submission.objects.filter(user=user, submission_date__gte=today_start).first()
            if submission:
                data['submission_content'] = submission.content
                data['submission_id'] = submission.id
        
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
            # Allow updating existing submission for today
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            existing_submission = Submission.objects.filter(user=user, submission_date__gte=today_start).first()
            
            # Proceed with submission or update
            current_day = user.current_experiment_day
            
            if existing_submission:
                serializer = DailySubmissionSerializer(existing_submission, data=request.data, context={'request': request}, partial=True)
            else:
                serializer = DailySubmissionSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                try:
                    serializer.save(user=user, experiment_day=current_day)
                except IntegrityError:
                    return Response(
                        {"detail": "You have already made a submission for today or for this experiment day."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Update Redis cache to reflect submission
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
    serializer_class = SubmissionSerializer

    def get_queryset(self):
        return Submission.objects.filter(user=self.request.user).order_by('-submission_date')

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response(
                {"detail": "You have already made a submission for today or for this experiment day."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_create(self, serializer):
        user = self.request.user
        current_day = user.current_experiment_day
        serializer.save(user=user, experiment_day=current_day)
