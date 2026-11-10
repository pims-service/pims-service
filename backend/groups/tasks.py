import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

from .models import Group
from .services import assign_user_to_group, alert_admins_if_capacity_low

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_group_capacity_alert_task(self, free_places: int):
    User = get_user_model()
    waiting = User.objects.filter(
        group__isnull=True,
        has_completed_sociodemographic=True,
        is_disqualified=False,
        is_staff=False,
    ).count()
    subject = f"[Psycheversity] Study groups almost full ({free_places} places left)"
    body = (
        f"Free places across all active study groups: {free_places}.\n"
        f"Eligible participants waiting for a group: {waiting}.\n\n"
        "New participants can still finish onboarding, but they are only assigned to a group "
        "(and only see daily activities) once a place is free.\n"
        "Increase capacity or add a group in the admin Groups page; waiting participants are "
        "assigned automatically within the hour."
    )
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [settings.SUPPORT_ADMIN_EMAIL], fail_silently=False)
        logger.info('Sent group capacity alert to %s (%s places left)', settings.SUPPORT_ADMIN_EMAIL, free_places)
        return {'status': 'sent', 'free_places': free_places, 'waiting': waiting}
    except Exception as exc:
        logger.error('Error sending group capacity alert: %s', exc)
        raise self.retry(exc=exc) from exc


@shared_task
def assign_unassigned_participants():
    """
    Assigns eligible participants who passed the screener while every group was full.
    Stops at the first capacity failure; admins are alerted (throttled).
    """
    User = get_user_model()
    pending = User.objects.filter(
        group__isnull=True,
        has_completed_sociodemographic=True,
        is_disqualified=False,
        is_staff=False,
    ).order_by('date_joined')

    assigned = 0
    for user in pending:
        try:
            assign_user_to_group(user)
            assigned += 1
        except Group.DoesNotExist:
            break

    alert_admins_if_capacity_low()
    # .all() re-queries: count() on the already-iterated queryset would return the stale cached length.
    remaining = pending.all().count()
    if assigned or remaining:
        logger.info('assign_unassigned_participants: assigned=%s still_waiting=%s', assigned, remaining)
    return {'assigned': assigned, 'still_waiting': remaining}
