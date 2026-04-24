import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from groups.models import Group
from phases.models import Phase
from activities.models import Activity
from django.utils import timezone

User = get_user_model()

def seed():
    # 1. Ensure Phase 2 exists
    phase = Phase.objects.first()
    if not phase:
        phase = Phase.objects.create(
            name='Phase 2: Experiment', 
            description='Main experiment phase', 
            phase_number=2,
            start_date=timezone.now().date(),
            end_date=timezone.now().date()
        )

    # 2. Grab an existing group (Control)
    grp = Group.objects.filter(name="Control").first()
    if not grp:
        grp = Group.objects.first()

    # 3. Create the Activity for this group
    activity_desc = "Before going to sleep, write down the following:\n• One thing that gave you pleasure today\n• One thing you were deeply absorbed in\n• One meaningful interaction with someone\n• One thing that felt purposeful\n• One thing you accomplished\n• One thing you are genuinely grateful for today"
    
    act, created = Activity.objects.update_or_create(
        group=grp,
        title="Combined PERMA & Gratitude task",
        defaults={
            'description': activity_desc,
            'activity_type': 'paragraph',
            'assigned_phase': phase,
            'day_number': 1
        }
    )

    # 4. Assign ALL users to this group so testuser will see it
    users = User.objects.all()
    count = 0
    for u in users:
        u.group = grp
        u.save()
        count += 1

    print(f"Success! Created activity '{act.title}' and assigned {count} users to '{grp.name}'.")

if __name__ == '__main__':
    seed()
