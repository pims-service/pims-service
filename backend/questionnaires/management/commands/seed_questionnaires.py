from django.core.management.base import BaseCommand
from questionnaires.models import Questionnaire, Question, Option
import uuid

class Command(BaseCommand):
    help = 'Seeds the database with a high-quality initial baseline questionnaire'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Initial Baseline Questionnaire...")

        # 1. Clear existing data if necessary (Optional, but good for idempotency)
        # We'll skip clearing for now to be safe, or just check for existence.
        q_title = "Initial Baseline Assessment v1"
        if Questionnaire.objects.filter(title=q_title).exists():
            self.stdout.write(self.style.WARNING(f"Questionnaire '{q_title}' already exists. Skipping."))
            return

        # 2. Create the Questionnaire
        questionnaire = Questionnaire.objects.create(
            title=q_title,
            description="A comprehensive initial assessment to determine experimental group eligibility and capture baseline psychometric data.",
            is_active=True,
            is_baseline=True
        )

        # 3. Define Questions
        questions_data = [
            {
                "content": "What is your primary field of study or profession?",
                "type": "CHOICE",
                "order": 1,
                "options": [
                    ("STEM (Science, Tech, Engineering, Math)", 1),
                    ("Arts & Humanities", 2),
                    ("Social Sciences", 3),
                    ("Business & Law", 4),
                    ("Other", 5)
                ]
            },
            {
                "content": "On a scale of 1 to 7, how frequently do you experience digital fatigue during high-intensity tasks?",
                "type": "SCALE",
                "order": 2,
                "options": [
                    ("1 - Never", 1),
                    ("2", 2),
                    ("3", 3),
                    ("4 - Neutral", 4),
                    ("5", 5),
                    ("6", 6),
                    ("7 - Always", 7)
                ]
            },
            {
                "content": "On a scale of 1 to 7, how focused do you feel when working in a synchronized group environment?",
                "type": "SCALE",
                "order": 3,
                "options": [
                    ("1 - Not focused at all", 1),
                    ("2", 2),
                    ("3", 3),
                    ("4 - Neutral", 4),
                    ("5", 5),
                    ("6", 6),
                    ("7 - Extremely focused", 7)
                ]
            },
            {
                "content": "Which platform do you primarily use for online collaboration?",
                "type": "CHOICE",
                "order": 4,
                "options": [
                    ("Slack / Discord", 1),
                    ("Microsoft Teams", 2),
                    ("WhatsApp / Telegram", 3),
                    ("Other / None", 4)
                ]
            },
            {
                "content": "Please describe your current feelings regarding group synchronization in three sentences.",
                "type": "TEXT",
                "order": 5,
                "options": []
            }
        ]

        # 4. Save Questions and Options
        for q_data in questions_data:
            q = Question.objects.create(
                questionnaire=questionnaire,
                content=q_data["content"],
                type=q_data["type"],
                order=q_data["order"]
            )
            
            for opt_label, opt_val in q_data["options"]:
                Option.objects.create(
                    question=q,
                    label=opt_label,
                    numeric_value=opt_val,
                    order=opt_val # Using numeric value for order in scales to keep them linear
                )

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded '{q_title}' with {len(questions_data)} questions."))
