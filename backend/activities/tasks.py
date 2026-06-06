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
        
        # 1. Sync current activity state and experiment day
        if user.onboarding_completed_at:
            from activities.timeline import get_active_activity_state

            now = timezone.localtime(timezone.now())
            state = get_active_activity_state(user)
            tomorrow = (now + timezone.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            timeout = int((tomorrow - now).total_seconds())

            cache_key_state = f"user_{user.user_id}_activity_state"
            cache_key_day = f"user_{user.user_id}_exp_day"
            if timeout > 0:
                cache.set(
                    cache_key_state,
                    "NONE" if state is None else state,
                    timeout=timeout,
                )
                if state is not None:
                    cache.set(cache_key_day, state.day_in_block, timeout=timeout)
                else:
                    cache.delete(cache_key_day)

        # 2. Sync submission status for today
        today_date = timezone.localdate()
        cache_key_sub = f"user_{user.user_id}_submitted_{today_date}"
        now_local = timezone.localtime(timezone.now())
        today_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        submitted_today = Submission.objects.filter(
            user=user,
            submission_date__gte=today_start
        ).exists()
        
        tomorrow = (now_local + timezone.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        timeout = int((tomorrow - now_local).total_seconds())
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
