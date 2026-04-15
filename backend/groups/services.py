from django.db.models import Count

from .models import Group


def assign_group():
    """
    Finds the group with the fewest participants.
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

def assign_user_to_group(user):
    """
    Assigns a specific user to the appropriate group based on current distribution.
    """
    if user.group is not None:
        return user.group
        
    group = assign_group()
    user.group = group
    user.save(update_fields=['group'])
    return group
