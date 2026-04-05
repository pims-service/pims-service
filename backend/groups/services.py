from django.db.models import Count

from .models import Group


def assign_group():
    """
    Return the Group with the fewest participants for balanced assignment.

    Uses a least-filled strategy: annotates each group with its current
    participant count and returns the one with the lowest count.
    Ties are broken deterministically by primary key.

    Raises:
        Group.DoesNotExist: If no groups are available for assignment.
    """
    group = (
        Group.objects
        .annotate(current_count=Count('participants'))
        .order_by('current_count', 'pk')
        .first()
    )

    if group is None:
        raise Group.DoesNotExist("No groups available for assignment.")

    return group
