import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from support.models import SupportTicket
from users.models import Role, User

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds fake participants and outreach call protocol follow-up tickets (Tiers 3 & 4) for dashboard testing'

    def handle(self, *args, **options):
        self.stdout.write('Starting Follow-Ups Seeding Engine...')

        # Ensure Participant role exists
        participant_role, _ = Role.objects.get_or_create(
            name='Participant',
            defaults={'description': 'Default role for experiment participants'}
        )

        fake_users_data = [
            {
                'username': 'john.doe',
                'email': 'john.doe@pims.local',
                'full_name': 'John Doe',
                'whatsapp_number': '+923123456789',
                'subject': 'Call Protocol: High Daily Activity Miss Rate (Tier 3)',
                'message': 'Participant John Doe has completed the 7-day active week but only submitted 1 daily activity. Please place a call within 72 hours using the supportive script.',
                'status': 'Open',
                'notes': 'Waiting for first outreach call attempt.'
            },
            {
                'username': 'jane.smith',
                'email': 'jane.smith@pims.local',
                'full_name': 'Jane Smith',
                'whatsapp_number': '+923987654321',
                'subject': 'Call Protocol: Assessment Overdue (3_MONTHS) - Tier 4',
                'message': 'Participant Jane Smith has not completed their Month 3 follow-up assessment, which is now 10 days overdue. Please place an outreach call.',
                'status': 'In Progress',
                'notes': 'Attempted contact on Day 10, phone went to voicemail. Left message.'
            },
            {
                'username': 'robert.johnson',
                'email': 'robert.j@pims.local',
                'full_name': 'Robert Johnson',
                'whatsapp_number': '+923111222333',
                'subject': 'Call Protocol: Assessment Overdue (7_DAYS) - Tier 4',
                'message': 'Participant Robert Johnson has not completed their 7-day posttest assessment, which is now 10 days overdue.',
                'status': 'Resolved',
                'notes': 'Spoke with Robert on Day 11. He was busy but completed the assessment during our call. Closed ticket.'
            }
        ]

        count = 0
        for data in fake_users_data:
            # Create user if not exists
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'full_name': data['full_name'],
                    'whatsapp_number': data['whatsapp_number'],
                    'role': participant_role,
                    'has_completed_sociodemographic': True,
                    'onboarding_completed_at': timezone.now() - timezone.timedelta(days=30),
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f"Created fake participant: {data['full_name']}")

            # Create or update follow-up support ticket
            ticket, ticket_created = SupportTicket.objects.get_or_create(
                user=user,
                subject=data['subject'],
                defaults={
                    'message': data['message'],
                    'status': data['status'],
                    'admin_notes': data['notes'],
                    'is_read_by_user': True
                }
            )
            if ticket_created:
                count += 1
                self.stdout.write(f"Created call ticket: {data['subject']} (Status: {data['status']})")

        # Create a user with consecutive missed days for dashboard banner testing
        consec_user, created_consec = User.objects.get_or_create(
            username='missed.user',
            defaults={
                'email': 'missed@pims.local',
                'full_name': 'Missed Day Participant',
                'whatsapp_number': '+923444555666',
                'role': participant_role,
                'has_completed_sociodemographic': True,
                'onboarding_completed_at': timezone.now() - timezone.timedelta(days=3),
            }
        )
        if created_consec:
            consec_user.set_password('password123')
            consec_user.save()
            self.stdout.write(self.style.SUCCESS("Created participant user with consecutive missed days: missed.user / password123"))
        else:
            # If they already exist, make sure their onboarding is reset so they are on Day 4
            consec_user.onboarding_completed_at = timezone.now() - timezone.timedelta(days=3)
            consec_user.save()
            self.stdout.write("Reset missed.user onboarding completed time to 3 days ago.")

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {count} fake Call Protocol follow-up tickets.'))
