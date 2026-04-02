import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def send_notification(self, notification_id):
    """Send a pending notification asynchronously and mark it as sent or failed."""
    from notifications.models import Notification

    try:
        notification = Notification.objects.get(pk=notification_id)
        logger.info(
            "Sending %s notification (id=%s) to user %s",
            notification.n_type,
            notification_id,
            notification.user_id,
        )
        notification.status = 'sent'
        notification.save(update_fields=['status'])
        return {'status': 'sent', 'notification_id': notification_id}
    except Notification.DoesNotExist:
        logger.error("Notification id=%s not found", notification_id)
        raise
    except Exception as exc:
        logger.error("Failed to send notification id=%s: %s", notification_id, exc)
        Notification.objects.filter(pk=notification_id).update(status='failed')
        raise self.retry(exc=exc, countdown=60, max_retries=3)
