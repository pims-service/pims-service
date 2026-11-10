from django.db.models import Count, F

from .models import Group

import logging
from django.db import transaction

logger = logging.getLogger(__name__)

def assign_group():
    """
    Finds the active group with the fewest participants that hasn't reached capacity.
    NOTE: Must be called within a transaction.atomic() block for concurrency safety.
    """
    # PostgreSQL doesn't allow select_for_update() with GROUP BY (from Count annotation).
    # So we find the candidate groups, then lock them one by one to verify capacity.
    candidates = list(
        Group.objects
        .filter(is_active=True)
        .annotate(current_count=Count('participants'))
        .order_by('current_count', 'pk')
    )

    for candidate in candidates:
        # Lock the row and re-verify actual capacity inside the lock
        locked_group = Group.objects.select_for_update().filter(pk=candidate.pk).first()
        if locked_group and locked_group.participants.count() < locked_group.capacity:
            return locked_group

    raise Group.DoesNotExist("No groups available for assignment (all inactive or at capacity).")


def assign_user_to_group(user):
    """
    Assigns a specific user to the appropriate group based on current distribution.
    Uses an atomic transaction to prevent race conditions.
    """
    if user.group is not None:
        return user.group
        
    with transaction.atomic():
        try:
            group = assign_group()
            user.group = group
            user.save(update_fields=['group'])
            return group
        except Exception as e:
            logger.error(f"Failed to assign user {user.username} to group: {e}")
            raise


# Free places (across all active groups) at or below which admins are warned.
LOW_CAPACITY_THRESHOLD = 20
# At most one capacity alert email per this many seconds.
CAPACITY_ALERT_INTERVAL = 6 * 60 * 60


def free_group_places():
    """Total remaining places across all active groups."""
    return sum(
        max(g.capacity - g.current_count, 0)
        for g in Group.objects.filter(is_active=True).annotate(current_count=Count('participants'))
    )


def alert_admins_if_capacity_low():
    """
    Queues a (throttled) admin email when free places drop to LOW_CAPACITY_THRESHOLD.
    Safe to call inside a transaction: the email is queued only after commit.
    """
    from django.core.cache import cache
    from .tasks import send_group_capacity_alert_task

    free = free_group_places()
    if free > LOW_CAPACITY_THRESHOLD:
        return
    # cache.add is atomic: only the first caller in the interval queues an email.
    if not cache.add('group_capacity_alert_sent', True, timeout=CAPACITY_ALERT_INTERVAL):
        return
    transaction.on_commit(lambda: send_group_capacity_alert_task.delay(free))


def try_assign_user_to_group(user):
    """
    Like assign_user_to_group, but never raises when every group is full or inactive:
    the user is left unassigned (picked up later by assign_unassigned_participants)
    and admins are alerted. Returns the group, or None.
    """
    try:
        group = assign_user_to_group(user)
    except Group.DoesNotExist:
        logger.warning("No group capacity for user %s; left unassigned for later assignment.", user.username)
        alert_admins_if_capacity_low()
        return None
    alert_admins_if_capacity_low()
    return group
