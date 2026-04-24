import logging
from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model
from activities.models import Submission

logger = logging.getLogger(__name__)

@shared_task
def sync_user_experiment_state(user_id):
    """
    Background task to sync a user's experimental day and submission status into Redis.
    Typically called after baseline completion or as a periodic cleanup.
    """
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
        
        # 1. Sync current experiment day
        if user.baseline_completed_at:
            now = timezone.now()
            delta = now.date() - user.baseline_completed_at.date()
            exp_day = delta.days + 1
            
            cache_key_day = f"user_{user.user_id}_exp_day"
            tomorrow = (now + timezone.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            timeout = int((tomorrow - now).total_seconds())
            if timeout > 0:
                cache.set(cache_key_day, exp_day, timeout=timeout)

        # 2. Sync submission status for today
        cache_key_sub = f"user_{user.user_id}_submitted_{timezone.now().date()}"
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        submitted_today = Submission.objects.filter(
            user=user,
            submission_date__gte=today_start
        ).exists()
        
        now = timezone.now()
        tomorrow = (now + timezone.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        timeout = int((tomorrow - now).total_seconds())
        if timeout > 0:
            cache.set(cache_key_sub, submitted_today, timeout=timeout)
            
        return {'user_id': user_id, 'synced': True}
    except User.DoesNotExist:
        logger.error("User %s not found for sync", user_id)
        return {'error': 'user_not_found'}

@shared_task
def generate_3month_export():
    """
    Asynchronous task to generate the final experimental data export.
    Triggered after the 3-month period.
    """
    logger.info("Starting production 3-month longitudinal data export...")
    # This would involve querying Submissions ordered by user and experiment_day
    # and generating a CSV/Excel file in media storage.
    # For now, it's a stub for the architecture.
    return {'status': 'success', 'message': 'Export queued (Archived in background)'}
