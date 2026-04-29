from django.db.models import Count, F

from .models import Group


def assign_group():
    """
    Finds the active group with the fewest participants that hasn't reached capacity.
    """
    group = (
        Group.objects
        .filter(is_active=True)
        .annotate(current_count=Count('participants'))
        .filter(current_count__lt=F('capacity'))
        .order_by('current_count', 'pk')
        .first()
    )

    if group is None:
        raise Group.DoesNotExist("No groups available for assignment (all inactive or at capacity).")

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
