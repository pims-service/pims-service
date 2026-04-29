import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from users.models import User, Role
from questionnaires.models import Questionnaire, Question, Option, ResponseSet, Response

class Command(BaseCommand):
    help = 'Seeds Day 7 Post-Test data and completions for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding post-test data...")

        # 1. Ensure a Post-Test Questionnaire exists
        posttest, created = Questionnaire.objects.get_or_create(
            title="Final Psychological Assessment (Day 7)",
            defaults={
                "description": "This is the mandatory follow-up assessment completed on the 7th day of the experiment.",
                "is_posttest": True,
                "is_active": True
            }
        )

        if created:
            self.stdout.write(f"Created post-test questionnaire: {posttest.title}")
            # Add some questions
            q1 = Question.objects.create(
                questionnaire=posttest,
                content="How much has your mood improved since the start of the experiment?",
                type="SCALE",
                order=1
            )
            for i in range(1, 6):
                Option.objects.create(question=q1, label=f"Level {i}", numeric_value=i, order=i)

            q2 = Question.objects.create(
                questionnaire=posttest,
                content="Would you recommend this experiment to others?",
                type="CHOICE",
                order=2
            )
            Option.objects.create(question=q2, label="Yes", numeric_value=1, order=1)
            Option.objects.create(question=q2, label="No", numeric_value=0, order=2)
        else:
            self.stdout.write(f"Post-test questionnaire already exists: {posttest.title}")

        # 2. Find or create users who are eligible for post-test (Day 7+)
        role_participant, _ = Role.objects.get_or_create(name='Participant')
        
        # Create 5 test users at Day 7
        for i in range(1, 6):
            username = f"day7_tester_{i}"
            user, u_created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.com",
                    "role": role_participant,
                    "has_completed_baseline": True,
                    "baseline_completed_at": timezone.now() - timedelta(days=7 + i)
                }
            )
            if u_created:
                user.set_password("password123")
                user.save()
                self.stdout.write(f"Created user: {username}")

            # 3. Create a completion for some of them
            if i <= 3: # 3 out of 5 have completed it
                rs, rs_created = ResponseSet.objects.get_or_create(
                    user=user,
                    questionnaire=posttest,
                    defaults={
                        "status": "COMPLETED",
                        "completed_at": timezone.now() - timedelta(hours=i*2)
                    }
                )
                if rs_created:
                    user.has_completed_posttest = True
                    user.posttest_completed_at = rs.completed_at
                    user.save(update_fields=['has_completed_posttest', 'posttest_completed_at'])
                    
                    # Add dummy responses
                    for question in posttest.questions.all():
                        if question.options.exists():
                            opt = random.choice(list(question.options.all()))
                            Response.objects.create(
                                response_set=rs,
                                question=question,
                                selected_option=opt
                            )
                    self.stdout.write(f"Created post-test completion for: {username}")

        self.stdout.write(self.style.SUCCESS("Successfully seeded post-test data!"))
