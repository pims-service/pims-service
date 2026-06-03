from django.core.management.base import BaseCommand
from activities.models import Activity
from groups.models import Group
from phases.models import Phase
from django.utils import timezone
from datetime import timedelta


# Default prompts for the 4 original research groups.
# Any group not listed here gets the fallback prompt.
GROUP_PROMPTS = {
    'Group 1': (
        "Today's task: Recall three different memories from your early childhood, before the age of 12. "
        "Write a brief description of each. They can be pleasant, neutral, or ordinary, anything you remember. "
        "Try to choose memories you have not written about earlier this week. Spend about 10 minutes total. | "
        "آج کا کام: اپنے بچپن کی، 12 سال کی عمر سے پہلے کی، تین مختلف یادیں ذہن میں لائیں۔ ہر ایک کی مختصر تفصیل لکھیں۔ "
        "یہ یادیں خوشگوار، عام، یا معمولی، کچھ بھی ہو سکتی ہیں — جو بھی یاد ہو۔ کوشش کریں کہ ایسی یادیں منتخب کریں جن کے "
        "بارے میں اس ہفتے پہلے نہ لکھا ہو۔ کل تقریباً 10 منٹ صرف کریں۔"
    ),
    'Group 2': (
        'Before going to sleep, write down three things you are genuinely grateful for today. '
        'They can be big or small — a person, a moment, a blessing, anything.'
    ),
    'Group 3': (
        'Before going to sleep, write down one thing from each of the following from your day:\n'
        '- Something that gave you pleasure or made you smile\n'
        '- Something you were so absorbed in you lost track of time\n'
        '- A meaningful interaction you had with someone\n'
        '- Something that felt purposeful or significant to you\n'
        '- Something you did well or accomplished today'
    ),
    'Group 4': (
        'Before going to sleep, write down the following:\n'
        '- One thing that gave you pleasure today\n'
        '- One thing you were deeply absorbed in\n'
        '- One meaningful interaction with someone\n'
        '- One thing that felt purposeful\n'
        '- One thing you accomplished\n'
        '- One thing you are genuinely grateful for today'
    ),
}

FALLBACK_PROMPT = (
    'Write a brief reflection about your day. '
    'What stood out to you? What are you thinking about?'
)

EXPERIMENT_DAYS = 7


class Command(BaseCommand):
    help = 'Seeds daily activities for ALL active groups for days 1-7'

    def handle(self, *args, **options):
        # 1. Ensure a Phase exists
        phase, _ = Phase.objects.get_or_create(
            phase_number=1,
            defaults={
                'name': 'Main Intervention Phase',
                'start_date': timezone.now().date(),
                'end_date': (timezone.now() + timedelta(days=30)).date()
            }
        )

        # 2. Ensure the 4 core research groups exist
        for group_name in GROUP_PROMPTS:
            Group.objects.get_or_create(name=group_name)

        # 3. Seed activities for EVERY active group, days 1-7
        groups = Group.objects.filter(is_active=True)
        total_created = 0

        for group in groups:
            prompt = GROUP_PROMPTS.get(group.name, FALLBACK_PROMPT)

            for day in range(1, EXPERIMENT_DAYS + 1):
                activity, created = Activity.objects.get_or_create(
                    group=group,
                    activity_type='paragraph',
                    day_number=day,
                    defaults={
                        'title': f'Daily Reflection - {group.name} - Day {day}',
                        'description': prompt,
                        'assigned_phase': phase,
                    }
                )

                if created:
                    total_created += 1
                else:
                    # Update existing prompt if it changed
                    if activity.description != prompt:
                        activity.description = prompt
                        activity.save(update_fields=['description'])
                        self.stdout.write(
                            f'Updated prompt for {group.name} Day {day}'
                        )

        self.stdout.write(self.style.SUCCESS(
            f'Done. Created {total_created} new activities across {groups.count()} groups × {EXPERIMENT_DAYS} days.'
        ))
