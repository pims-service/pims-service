import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from groups.models import Group
from phases.models import Phase
from activities.models import Activity

def seed():
    # Ensure current phase exists
    from django.utils import timezone
    phase = Phase.objects.first()
    if not phase:
        phase = Phase.objects.create(
            name='Phase 2: Experiment', 
            description='Main experiment phase', 
            phase_number=2,
            start_date=timezone.now().date(),
            end_date=timezone.now().date()
        )

    activities_data = [
        {
            "name": "Control Group",
            "title": "Daily Reflection",
            "desc": "Think of an early childhood memory and write it down in as much detail as you can remember."
        },
        {
            "name": "PERMA Group",
            "title": "Daily PERMA",
            "desc": "Before going to sleep, write down one thing from each of the following from your day:\n• Something that gave you pleasure or made you smile\n• Something you were so absorbed in you lost track of time\n• A meaningful interaction you had with someone\n• Something that felt purposeful or significant to you\n• Something you did well or accomplished today"
        },
        {
            "name": "Gratitude Group",
            "title": "Daily Gratitude",
            "desc": "Before going to sleep, write down three things you are genuinely grateful for today. They can be big or small — a person, a moment, a blessing, anything."
        },
        {
            "name": "Combined Group",
            "title": "Combined PERMA & Gratitude",
            "desc": "Before going to sleep, write down the following:\n• One thing that gave you pleasure today\n• One thing you were deeply absorbed in\n• One meaningful interaction with someone\n• One thing that felt purposeful\n• One thing you accomplished\n• One thing you are genuinely grateful for today"
        }
    ]

    for data in activities_data:
        grp, _ = Group.objects.get_or_create(name=data["name"], defaults={'capacity': 100, 'is_active': True})
        Activity.objects.update_or_create(
            group=grp,
            title=data["title"],
            defaults={
                'description': data["desc"],
                'activity_type': 'paragraph',
                'assigned_phase': phase,
                'day_number': 1
            }
        )
        print(f"Created group/activity for {data['name']}")

if __name__ == '__main__':
    seed()
