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
