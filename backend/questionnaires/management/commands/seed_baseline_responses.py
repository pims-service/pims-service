import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from questionnaires.models import Questionnaire, ResponseSet, Response, Question
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds high-fidelity dummy research data for both Sociodemographic and Psychometric (SIGNUP) baseline scales'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Unified Baseline Data Seeding Engine...'))

        # 1. Locate the new Questionnaires
        socio_q = Questionnaire.objects.filter(assessment_type='SOCIODEMOGRAPHIC', is_active=True).first()
        psy_q = Questionnaire.objects.filter(assessment_type='PSYCHOMETRIC', is_active=True).first()

        if not socio_q or not psy_q:
            self.stdout.write(self.style.ERROR('Required questionnaires (SOCIODEMOGRAPHIC or PSYCHOMETRIC) not found. Please run seed_longitudinal_scales first.'))
            return

        # 2. Get participants
        participants = User.objects.filter(is_superuser=False)
        if not participants.exists():
            self.stdout.write(self.style.WARNING('No participants found to seed. Using all available users.'))
            participants = User.objects.all()

        socio_questions = socio_q.questions.prefetch_related('options').all()
        psy_questions = psy_q.questions.prefetch_related('options').all()
        count = 0

        for user in participants:
            # GUARD: Do not overwrite realistic date/state for existing users who already completed baseline
            if user.has_completed_baseline and user.baseline_completed_at:
                continue

            # Generate realistic phone number if not present
            if not user.whatsapp_number:
                user.whatsapp_number = f"+923{random.randint(0,9)}{random.randint(1000000, 9999999)}"

            # Ensure they completed both
            user.has_completed_sociodemographic = True
            user.has_completed_baseline = True
            
            completion_time = timezone.now() - timedelta(days=random.randint(1, 7), hours=random.randint(0, 23))
            start_time = completion_time - timedelta(minutes=random.randint(5, 15))
            user.baseline_completed_at = completion_time
            user.save()

            # Seed Sociodemographic ResponseSet (no milestone required for socio)
            rs_socio, socio_created = ResponseSet.objects.get_or_create(
                user=user,
                questionnaire=socio_q,
                defaults={
                    'status': 'COMPLETED',
                    'started_at': start_time,
                    'completed_at': completion_time,
                    'milestone': None
                }
            )
            if socio_created:
                for question in socio_questions:
                    options = list(question.options.all())
                    if options:
                        # Prevent seeding disqualifying responses so dummy users stay active
                        valid_options = [opt for opt in options if 'DISQUALIFY' not in opt.label]
                        selected_opt = random.choice(valid_options) if valid_options else random.choice(options)
                        Response.objects.create(
                            response_set=rs_socio,
                            question=question,
                            selected_option=selected_opt
                        )

            # Seed Psychometric Baseline ResponseSet (SIGNUP milestone)
            rs_psy, psy_created = ResponseSet.objects.get_or_create(
                user=user,
                questionnaire=psy_q,
                milestone='SIGNUP',
                defaults={
                    'status': 'COMPLETED',
                    'started_at': start_time,
                    'completed_at': completion_time
                }
            )
            if psy_created:
                for question in psy_questions:
                    options = list(question.options.all())
                    if options:
                        Response.objects.create(
                            response_set=rs_psy,
                            question=question,
                            selected_option=random.choice(options)
                        )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded unified baseline dummy data for {count} participants.'))
