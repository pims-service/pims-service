from django.core.management.base import BaseCommand
from questionnaires.models import Questionnaire, Question, Option

class Command(BaseCommand):
    help = 'Seeds the database with the new Sociodemographic Form and the combined Longitudinal Psychometric Battery'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Longitudinal Scale Questionnaires...")

        # 1. Seed Sociodemographic Form
        socio_title = "Sociodemographic Survey"
        
        # Always recreate the sociodemographic form to ensure it matches the 12-item schema
        Questionnaire.objects.filter(title=socio_title).delete()
        
        if not Questionnaire.objects.filter(title=socio_title).exists():
            socio_q = Questionnaire.objects.create(
                title=socio_title,
                description="Collected once on signup to understand participant background. Items 11 and 12 are eligibility screeners.",
                is_active=True,
                assessment_type='SOCIODEMOGRAPHIC'
            )
            
            socio_data = [
                {
                    "content": "Age | عمر",
                    "type": "CHOICE",
                    "order": 1,
                    "options": [("18–25", 1), ("26–35", 2), ("36–45", 3), ("46–55", 4), ("56–65", 5), ("65+", 6)]
                },
                {
                    "content": "Gender | جنس",
                    "type": "CHOICE",
                    "order": 2,
                    "options": [("Male", 1), ("Female", 2), ("Prefer not to say", 3)]
                },
                {
                    "content": "Province / Region of Residence | رہائشی صوبہ / علاقہ",
                    "type": "CHOICE",
                    "order": 3,
                    "options": [("Punjab", 1), ("Sindh", 2), ("KPK", 3), ("Balochistan", 4), ("AJK", 5), ("GB", 6), ("ICT", 7), ("Other", 8)]
                },
                {
                    "content": "Highest Level of Education Completed | اعلیٰ ترین تعلیمی قابلیت",
                    "type": "CHOICE",
                    "order": 4,
                    "options": [("None", 1), ("Primary-Middle", 2), ("Matric", 3), ("Inter-A-Lvl", 4), ("Bachelor", 5), ("Master", 6), ("PhD", 7)]
                },
                {
                    "content": "Current Employment Status | موجودہ ملازمت کی صورتحال",
                    "type": "CHOICE",
                    "order": 5,
                    "options": [("Full-time", 1), ("Part-time", 2), ("Self-employed", 3), ("Student", 4), ("Homemaker", 5), ("Unemployed", 6), ("Retired", 7)]
                },
                {
                    "content": "Monthly Household Income (PKR) | ماہانہ گھریلو آمدنی",
                    "type": "CHOICE",
                    "order": 6,
                    "options": [("<30k", 1), ("30–60k", 2), ("60–100k", 3), ("100–150k", 4), ("150–250k", 5), (">250k", 6), ("Prefer not", 7)]
                },
                {
                    "content": "Current Marital Status | موجودہ ازدواجی حیثیت",
                    "type": "CHOICE",
                    "order": 7,
                    "options": [("Single", 1), ("Married", 2), ("Divorced", 3), ("Widowed", 4), ("Separated", 5)]
                },
                {
                    "content": "Current Living Arrangement | موجودہ رہائشی انتظام",
                    "type": "CHOICE",
                    "order": 8,
                    "options": [("Alone", 1), ("Spouse only", 2), ("Immediate family", 3), ("Joint family", 4), ("Flatmates", 5), ("Other", 6)]
                },
                {
                    "content": "Primary Internet Device | انٹرنیٹ تک رسائی کا بنیادی آلہ",
                    "type": "CHOICE",
                    "order": 9,
                    "options": [("Smartphone", 1), ("Computer", 2), ("Both", 3), ("Tablet", 4), ("Other", 5)]
                },
                {
                    "content": "Internet Access Frequency | آپ انٹرنیٹ کتنی بار استعمال کرتے ہیں؟",
                    "type": "CHOICE",
                    "order": 10,
                    "options": [("Multiple/day", 1), ("Once/day", 2), ("Few/week", 3), ("Rarely", 4)]
                },
                {
                    "content": "Currently taking psychotropic medication? | کیا آپ نفسیاتی دوائی لے رہے ہیں؟",
                    "type": "CHOICE",
                    "order": 11,
                    "options": [("Yes -> DISQUALIFY", 1), ("No", 2)]
                },
                {
                    "content": "Currently receiving psychotherapy or counselling? | کیا آپ سائیکو تھراپی حاصل کر رہے ہیں؟",
                    "type": "CHOICE",
                    "order": 12,
                    "options": [("Yes -> DISQUALIFY", 1), ("No", 2)]
                }
            ]
            self._create_questions_for_questionnaire(socio_q, socio_data)
            self.stdout.write(self.style.SUCCESS(f"Successfully seeded '{socio_title}'."))

        # 2. Seed Combined Longitudinal Psychometric Battery
        battery_title = "Longitudinal Psychometric Scales"
        if not Questionnaire.objects.filter(title=battery_title).exists():
            battery_q = Questionnaire.objects.create(
                title=battery_title,
                description="Standardized psychological scales (PERMA + PHQ-9 + GAD-7 + PANAS + GQ-6 + SIDAS) administered at specific milestones.",
                is_active=True,
                assessment_type='PSYCHOMETRIC'
            )

            # Define clinical scale options
            scale_0_to_10 = [(f"{i}", i) for i in range(11)]
            scale_0_to_10[0] = ("0 - Not at all / Never", 0)
            scale_0_to_10[10] = ("10 - Completely / Always", 10)

            phq_gad_options = [
                ("0 - Not at all", 0),
                ("1 - Several days", 1),
                ("2 - More than half the days", 2),
                ("3 - Nearly every day", 3)
            ]

            panas_options = [
                ("1 - Very slightly or not at all", 1),
                ("2 - A little", 2),
                ("3 - Moderately", 3),
                ("4 - Quite a bit", 4),
                ("5 - Extremely", 5)
            ]

            gq6_options = [
                ("1 - Strongly disagree", 1),
                ("2", 2),
                ("3", 3),
                ("4 - Neutral", 4),
                ("5", 5),
                ("6", 6),
                ("7 - Strongly agree", 7)
            ]

            battery_data = [
                # --- PERMA Profiler questions (Sample) ---
                {
                    "content": "[PERMA] In general, how often do you feel joyful?",
                    "type": "SCALE",
                    "order": 1,
                    "options": scale_0_to_10
                },
                {
                    "content": "[PERMA] In general, how active and vigorous are you?",
                    "type": "SCALE",
                    "order": 2,
                    "options": scale_0_to_10
                },
                # --- PHQ-9 questions (Sample) ---
                {
                    "content": "[PHQ-9] Little interest or pleasure in doing things.",
                    "type": "SCALE",
                    "order": 3,
                    "options": phq_gad_options
                },
                {
                    "content": "[PHQ-9] Feeling down, depressed, or hopeless.",
                    "type": "SCALE",
                    "order": 4,
                    "options": phq_gad_options
                },
                # --- GAD-7 questions (Sample) ---
                {
                    "content": "[GAD-7] Feeling nervous, anxious or on edge.",
                    "type": "SCALE",
                    "order": 5,
                    "options": phq_gad_options
                },
                {
                    "content": "[GAD-7] Not being able to stop or control worrying.",
                    "type": "SCALE",
                    "order": 6,
                    "options": phq_gad_options
                },
                # --- PANAS questions (Sample) ---
                {
                    "content": "[PANAS] To what extent do you feel inspired?",
                    "type": "SCALE",
                    "order": 7,
                    "options": panas_options
                },
                {
                    "content": "[PANAS] To what extent do you feel nervous?",
                    "type": "SCALE",
                    "order": 8,
                    "options": panas_options
                },
                # --- GQ-6 questions (Sample) ---
                {
                    "content": "[GQ-6] I have so much in life to be thankful for.",
                    "type": "SCALE",
                    "order": 9,
                    "options": gq6_options
                },
                # --- SIDAS questions (Sample) ---
                {
                    "content": "[SIDAS] In the past month, how often have you had thoughts of suicide?",
                    "type": "SCALE",
                    "order": 10,
                    "options": scale_0_to_10
                }
            ]
            self._create_questions_for_questionnaire(battery_q, battery_data)
            self.stdout.write(self.style.SUCCESS(f"Successfully seeded '{battery_title}'."))
        else:
            self.stdout.write(self.style.WARNING(f"'{battery_title}' already exists. Skipping."))

    def _create_questions_for_questionnaire(self, questionnaire, data):
        for q_data in data:
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
                    order=opt_val
                )
