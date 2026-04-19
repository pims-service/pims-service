from django.core.management.base import BaseCommand
from activities.models import Activity
from groups.models import Group
from phases.models import Phase
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Seeds the default daily activities for the 4 research groups'

    def handle(self, *args, **options):
        # 1. Ensure a Phase exists
        phase, created = Phase.objects.get_or_create(
            phase_number=1,
            defaults={
                'name': 'Main Intervention Phase',
                'start_date': timezone.now().date(),
                'end_date': (timezone.now() + timedelta(days=30)).date()
            }
        )

        # 2. Define Groups and Prompts
        group_data = [
            {
                'name': 'Control',
                'prompt': 'Think of an early childhood memory and write it down in as much detail as you can remember.'
            },
            {
                'name': 'PERMA',
                'prompt': 'Before going to sleep, write down one thing from each of the following from your day:\n'
                          '- Something that gave you pleasure or made you smile\n'
                          '- Something you were so absorbed in you lost track of time\n'
                          '- A meaningful interaction you had with someone\n'
                          '- Something that felt purposeful or significant to you\n'
                          '- Something you did well or accomplished today'
            },
            {
                'name': 'Gratitude',
                'prompt': 'Before going to sleep, write down three things you are genuinely grateful for today. '
                          'They can be big or small — a person, a moment, a blessing, anything.'
            },
            {
                'name': 'Combined',
                'prompt': 'Before going to sleep, write down the following:\n'
                          '- One thing that gave you pleasure today\n'
                          '- One thing you were deeply absorbed in\n'
                          '- One meaningful interaction with someone\n'
                          '- One thing that felt purposeful\n'
                          '- One thing you accomplished\n'
                          '- One thing you are genuinely grateful for today'
            }
        ]

        for data in group_data:
            group, _ = Group.objects.get_or_create(name=data['name'])
            
            activity, created = Activity.objects.get_or_create(
                group=group,
                activity_type='paragraph',
                defaults={
                    'title': f'Daily Reflection - {group.name}',
                    'description': data['prompt'],
                    'assigned_phase': phase,
                    'day_number': 1
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created daily activity for {group.name}'))
            else:
                activity.description = data['prompt']
                activity.save()
                self.stdout.write(self.style.INFO(f'Updated daily activity for {group.name}'))

        self.stdout.write(self.style.SUCCESS('Successfully seeded daily tasks.'))
