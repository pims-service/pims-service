import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from questionnaires.models import Questionnaire, ResponseSet, Response, Question
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds high-fidelity fake research data for the Baseline Assessment terminal'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Research Data Seeding Engine...'))

        # 1. Locate Baseline Questionnaire
        baseline = Questionnaire.objects.filter(is_baseline=True).first()
        if not baseline:
            self.stdout.write(self.style.ERROR('No Baseline Questionnaire found. Please run seed_questionnaires first.'))
            return

        # 2. Get participants (excluding superusers for realistic data)
        participants = User.objects.filter(is_superuser=False)
        if not participants.exists():
            self.stdout.write(self.style.WARNING('No participants found to seed. Using all available users.'))
            participants = User.objects.all()

        questions = baseline.questions.prefetch_related('options').all()
        count = 0

        for user in participants:
            # Check if they already have a completed baseline
            if ResponseSet.objects.filter(user=user, questionnaire=baseline, status='COMPLETED').exists():
                continue

            # Create high-fidelity timestamp (randomly within the last 7 days)
            completion_time = timezone.now() - timedelta(days=random.randint(0, 7), hours=random.randint(0, 23))
            start_time = completion_time - timedelta(minutes=random.randint(5, 15))

            with timezone.override(timezone.get_current_timezone()):
                response_set = ResponseSet.objects.create(
                    user=user,
                    questionnaire=baseline,
                    status='COMPLETED',
                    started_at=start_time,
                    completed_at=completion_time
                )

                # Generate randomized responses
                for question in questions:
                    response_data = {
                        'response_set': response_set,
                        'question': question
                    }

                    if question.type in ['RADIO', 'SELECT']:
                        options = list(question.options.all())
                        if options:
                            response_data['selected_option'] = random.choice(options)
                    else:
                        response_data['text_value'] = f"Sample researcher insight for participant {user.username} regarding {question.content[:20]}..."

                    Response.objects.create(**response_data)
                
                # Mark user as having completed baseline
                user.has_completed_baseline = True
                user.save(update_fields=['has_completed_baseline'])
                
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {count} high-fidelity baseline assessments.'))
