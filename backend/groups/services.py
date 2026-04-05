from django.db.models import Count

from .models import Group


def assign_group():

    group = (
        Group.objects
        .annotate(current_count=Count('participants'))
        .order_by('current_count', 'pk')
        .first()
    )

    if group is None:
        raise Group.DoesNotExist("No groups available for assignment.")

    return group
