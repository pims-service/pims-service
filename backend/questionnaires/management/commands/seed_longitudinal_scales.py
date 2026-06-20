from django.core.management.base import BaseCommand
from questionnaires.models import Questionnaire, Question, Option

class Command(BaseCommand):
    help = 'Seeds the database with the new Sociodemographic Form and the combined Longitudinal Psychometric Battery'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Longitudinal Scale Questionnaires...")

        # Delete legacy questionnaires that are no longer used (only if they have no response sets)
        self.stdout.write("Checking for legacy questionnaires...")
        legacy_qs = Questionnaire.objects.exclude(title__in=["Sociodemographic Survey", "Longitudinal Psychometric Scales"])
        for legacy_q in legacy_qs:
            if not legacy_q.attempts.exists():
                self.stdout.write(f"Deleting unused legacy questionnaire: {legacy_q.title}")
                legacy_q.delete()
            else:
                self.stdout.write(self.style.WARNING(f"Keeping legacy questionnaire '{legacy_q.title}' because it has active response data."))

        # 1. Seed Sociodemographic Form
        socio_title = "Sociodemographic Survey"

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
                "options": [("Yes", 1), ("No", 2)]
            },
            {
                "content": "Currently receiving psychotherapy or counselling? | کیا آپ سائیکو تھراپی حاصل کر رہے ہیں؟",
                "type": "CHOICE",
                "order": 12,
                "options": [("Yes", 1), ("No", 2)]
            }
        ]

        socio_q, socio_created = Questionnaire.objects.get_or_create(
            title=socio_title,
            defaults={
                "description": "Collected once on signup to understand participant background. Items 11 and 12 are eligibility screeners.",
                "is_active": True,
                "assessment_type": 'SOCIODEMOGRAPHIC',
            }
        )
        if socio_created:
            self.stdout.write(self.style.SUCCESS(f"Created '{socio_title}'."))
        else:
            self.stdout.write(self.style.WARNING(f"'{socio_title}' exists — syncing questions in-place."))
        self._sync_questions_for_questionnaire(socio_q, socio_data)

        # 2. Seed Combined Longitudinal Psychometric Battery
        battery_title = "Longitudinal Psychometric Scales"

        # Ensure no other questionnaire is marked as the post-test to avoid conflicts
        Questionnaire.objects.filter(is_posttest=True).update(is_posttest=False)

        battery_q, battery_created = Questionnaire.objects.get_or_create(
            title=battery_title,
            defaults={
                "description": "Standardized psychological scales (PERMA + PHQ-9 + GAD-7 + PANAS + GQ-6 + SIDAS) administered at specific milestones.",
                "is_active": True,
                "is_posttest": True,
                "assessment_type": 'PSYCHOMETRIC',
            }
        )
        # Always keep is_posttest=True on the battery (may have been cleared above)
        if not battery_q.is_posttest:
            battery_q.is_posttest = True
            battery_q.save(update_fields=["is_posttest"])
        if battery_created:
            self.stdout.write(self.style.SUCCESS(f"Created '{battery_title}'."))
        else:
            self.stdout.write(self.style.WARNING(f"'{battery_title}' exists — syncing questions in-place."))

        if True:  # always runs (idempotent)
            battery_q = battery_q  # alias kept for block below

            # Define clinical scale options
            scale_0_to_10 = [(f"{i}", i) for i in range(11)]
            scale_0_to_10[0] = ("0 - Not at all / Never | بالکل نہیں / کبھی نہیں", 0)
            scale_0_to_10[10] = ("10 - Completely / Always | مکمل طور پر / ہمیشہ", 10)

            opts_never_always = [(f"{i}", i) for i in range(11)]
            opts_never_always[0] = ("0 - Never | کبھی نہیں", 0)
            opts_never_always[10] = ("10 - Always | ہمیشہ", 10)

            opts_terrible_excellent = [(f"{i}", i) for i in range(11)]
            opts_terrible_excellent[0] = ("0 - Terrible | انتہائی خراب", 0)
            opts_terrible_excellent[10] = ("10 - Excellent | بہترین", 10)

            opts_notatall_completely = [(f"{i}", i) for i in range(11)]
            opts_notatall_completely[0] = ("0 - Not at all | بالکل بھی نہیں", 0)
            opts_notatall_completely[10] = ("10 - Completely | مکمل طور پر", 10)

            phq_options = [
                ("0 - Not at all | بالکل نہیں", 0),
                ("1 - Several days | کئی دن", 1),
                ("2 - More than half the days | ایک ہفتے سے زیادہ", 2),
                ("3 - Nearly every day | تقریباً روزانہ", 3)
            ]



            panas_options = [
                ("0 - Very slightly or not at all | کبھی نہیں", 0),
                ("1 - A little | بہت کم", 1),
                ("2 - Moderately | درمیانہ", 2),
                ("3 - Quite a bit | کافی حد تک", 3),
                ("4 - Extremely | بہت زیادہ", 4)
            ]

            grat_options = [
                ("0 - Completely disagree | بالکل غیر متفق", 0),
                ("1 - Disagree | غیر متفق", 1),
                ("2 - Neutral | غیر جانبدار", 2),
                ("3 - Agree | متفق", 3),
                ("4 - Completely agree | مکمل متفق", 4)
            ]

            sidas_options_1 = [(f"{i}", i) for i in range(11)]
            sidas_options_1[0] = ("0 - Never | کبھی نہیں", 0)
            sidas_options_1[10] = ("10 - Always | ہمیشہ", 10)

            sidas_options_2 = [(f"{i}", i) for i in range(11)]
            sidas_options_2[0] = ("0 - No control | بالکل قابو نہیں", 0)
            sidas_options_2[10] = ("10 - Full control | مکمل قابو", 10)

            sidas_options_3 = [(f"{i}", i) for i in range(11)]
            sidas_options_3[0] = ("0 - Not close at all | بالکل قریب نہیں", 0)
            sidas_options_3[10] = ("10 - Made an attempt | ایک کوشش کی", 10)

            sidas_options_4_5 = [(f"{i}", i) for i in range(11)]
            sidas_options_4_5[0] = ("0 - Not at all | بالکل نہیں", 0)
            sidas_options_4_5[10] = ("10 - Extremely | بہت زیادہ", 10)

            battery_data = [
                # --- 23-Item PERMA Profiler ---
                {
                    "content": "[PERMA] How much of the time do you feel you are making progress towards accomplishing your goals? | آپ کو کتنی بار لگتا ہے کہ آپ اپنے مقاصد کی طرف بڑھ رہے ہیں؟",
                    "type": "SCALE",
                    "order": 1,
                    "options": opts_never_always
                },
                {
                    "content": "[PERMA] How often do you become absorbed in what you are doing? | آپ کتنی بار اپنے کام میں پوری طرح مشغول ہو جاتے ہیں؟",
                    "type": "SCALE",
                    "order": 2,
                    "options": opts_never_always
                },
                {
                    "content": "[PERMA] In general, how often do you feel joyful? | عام طور پر، آپ کتنی بار خوشگوار / خوشی محسوس کرتے ہیں؟",
                    "type": "SCALE",
                    "order": 3,
                    "options": opts_never_always
                },
                {
                    "content": "[PERMA] In general, how often do you feel anxious? | عام طور پر، آپ کتنی باربے چین/  بے چینی محسوس کرتے ہیں؟",
                    "type": "SCALE",
                    "order": 4,
                    "options": opts_never_always
                },
                {
                    "content": "[PERMA] How often do you achieve the important goals you have set for yourself? | کتنی بارآپ اپنے لیے مقرر کردہ اہم اہداف/ مقاصد کو حاصل کرتے ہیں؟",
                    "type": "SCALE",
                    "order": 5,
                    "options": opts_never_always
                },
                {
                    "content": "[PERMA] In general, how would you say your health is? | عام طور پر، آپ اپنی صحت کو کیسا محسوس کرتے ہیں؟",
                    "type": "SCALE",
                    "order": 6,
                    "options": opts_terrible_excellent
                },
                {
                    "content": "[PERMA] In general, to what extent do you lead a purposeful and meaningful life? | عام طورپر، آپ کس حد تک بامقصد اور با معنی زندگی گزارتے ہیں؟",
                    "type": "SCALE",
                    "order": 7,
                    "options": opts_notatall_completely
                },
                {
                    "content": "[PERMA] To what extent do you receive help and support from others when you need it? | آپ کو ضرورت پڑنے پر دوسروں سے کتنی مدد اور حمایت ملتی ہے؟",
                    "type": "SCALE",
                    "order": 8,
                    "options": opts_notatall_completely
                },
                {
                    "content": "[PERMA] In general, to what extent do you feel that what you do in your life is valuable and worthwhile? | عام طور پر، آپ کس حد تک محسوس کرتے ہیں کہ آپ اپنی زندگی میں جو کچھ کرتے ہیں وہ قیمتی اورقابل قدر ہے؟",
                    "type": "SCALE",
                    "order": 9,
                    "options": opts_notatall_completely
                },
                {
                    "content": "[PERMA] In general, to what extent do you feel excited and interested in things? | عام طور پر، آپ کو چیزوں میں کتنی دلچسپی اور جوش و خروش محسوس ہوتا ہے؟",
                    "type": "SCALE",
                    "order": 10,
                    "options": opts_notatall_completely
                },
                {
                    "content": "[PERMA] How lonely do you feel in your daily life? | آپ اپنی روزمرہ زندگی میں خود کو کتنا تنہا محسوس کرتے ہیں؟",
                    "type": "SCALE",
                    "order": 11,
                    "options": opts_notatall_completely
                },
                {
                    "content": "[PERMA] How satisfied are you with your current physical health? | آپ اپنی موجودہ جسمانی صحت سے کتنے مطمئن ہیں؟",
                    "type": "SCALE",
                    "order": 12,
                    "options": opts_notatall_completely
                },
                {
                    "content": "[PERMA] In general, how often do you feel positive? | عام طور پر، آپ کتنا  مثبت محسوس کرتے ہیں؟",
                    "type": "SCALE",
                    "order": 13,
                    "options": opts_never_always
                },
                {
                    "content": "[PERMA] In general, how often do you feel angry? | عام طور پر ، آپ کتنی بار غصہ محسوس کرتے ہیں ؟",
                    "type": "SCALE",
                    "order": 14,
                    "options": opts_never_always
                },
                {
                    "content": "[PERMA] How often are you able to handle your responsibilities? | عام طور پر، آپ اپنی ذمہ داریوں کو نبھانے کے کتنے قابل ہیں؟",
                    "type": "SCALE",
                    "order": 15,
                    "options": opts_never_always
                },
                {
                    "content": "[PERMA] In general, how often do you feel sad? | عام طور پر، آپ خود کو کتنی بار اداس محسوس کرتے ہیں؟",
                    "type": "SCALE",
                    "order": 16,
                    "options": opts_never_always
                },
                {
                    "content": "[PERMA] How often do you lose track of time while doing something you enjoy? | آپ کتنی بار اپنا پسندیدہ کام کرتے ہوئے وقت سے بے خبر ہو جاتے ہیں؟",
                    "type": "SCALE",
                    "order": 17,
                    "options": opts_never_always
                },
                {
                    "content": "[PERMA] Compared to others of your same age and sex, how is your health? | اپنی عمر اور جنس کے دوسرے لوگوں کے مقابلے میں، آپ کی صحت کیسی ہے؟",
                    "type": "SCALE",
                    "order": 18,
                    "options": opts_terrible_excellent
                },
                {
                    "content": "[PERMA] To what extent do you feel loved? | آپ کو کس حد تک محسوس ہوتا ہے کہ لوگ آپ سے پیار کرتے ہیں / آپ کو چاہتے ہیں؟",
                    "type": "SCALE",
                    "order": 19,
                    "options": opts_notatall_completely
                },
                {
                    "content": "[PERMA] To what extent do you generally feel you have a sense of direction in your life? | آپ کوکس حد تک محسوس ہوتا ہے کہ آپ کی زندگی کی کوئی  سمت / رخ ہے؟",
                    "type": "SCALE",
                    "order": 20,
                    "options": opts_notatall_completely
                },
                {
                    "content": "[PERMA] How satisfied are you with your personal relationships? | آپ اپنے ذاتی تعلقات / رشتوں سے کتنے مطمئن ہیں؟",
                    "type": "SCALE",
                    "order": 21,
                    "options": opts_notatall_completely
                },
                {
                    "content": "[PERMA] In general, to what extent do you feel contented? | عام طور پر، آپ کس حد تک مطمئن محسوس کرتے ہیں؟",
                    "type": "SCALE",
                    "order": 22,
                    "options": opts_notatall_completely
                },
                {
                    "content": "[PERMA] Taking all things together, how happy would you say you are? | مجموعی طور پر/ تمام چیزوں کو ملاکر، آپ اپنے آپ کو کتنا خوش پاتے ہیں؟",
                    "type": "SCALE",
                    "order": 23,
                    "options": opts_notatall_completely
                },
                # --- 9-Item PHQ-9 ---
                # Section header (bilingual, display-only, not scored)
                {
                    "content": "[PHQ-9] Over the past two weeks, how much have you been bothered by the following problems? | گزشتہ دو ہفتوں کے دوران مندرجہ ذیل مسائل سے آپ کتنا پریشان ہوئے؟",
                    "type": "TEXT",
                    "order": 24,
                    "required": False,
                    "options": []
                },
                # PHQ-9 items: orders 25-33
                {
                    "content": "[PHQ-9] Little interest or pleasure in doing things | روزمرہ کے کاموں میں دلچسپی یا لطف کی کمی۔",
                    "type": "SCALE",
                    "order": 25,
                    "options": phq_options
                },
                {
                    "content": "[PHQ-9] Feeling down, depressed, or hopeless | اداسی، افسردگی یا مایوسی کا احساس۔",
                    "type": "SCALE",
                    "order": 26,
                    "options": phq_options
                },
                {
                    "content": "[PHQ-9] Trouble falling or staying asleep, or sleeping too much | نیند سے متعلق مسائل: (الف) نیند نہ آنا (ب) نیند آنے کے بعد سوتے رہنے میں دشواری (ج) نیند کی زیادتی۔",
                    "type": "SCALE",
                    "order": 27,
                    "options": phq_options
                },
                {
                    "content": "[PHQ-9] Feeling tired or having little energy | بے سبب تھکاوٹ یا کمزوری کا احساس۔",
                    "type": "SCALE",
                    "order": 28,
                    "options": phq_options
                },
                {
                    "content": "[PHQ-9] Poor appetite or overeating | بلاوجہ بھوک میں کمی یا زیادتی۔",
                    "type": "SCALE",
                    "order": 29,
                    "options": phq_options
                },
                {
                    "content": "[PHQ-9] Feeling bad about yourself or that you are a failure or have let yourself or your family down | شکست خوردگی یا ناکامی کا احساس، یا یہ محسوس ہونا کہ آپ اپنے خاندان کی توقعات پر پورا نہیں اترے۔",
                    "type": "SCALE",
                    "order": 30,
                    "options": phq_options
                },
                {
                    "content": "[PHQ-9] Trouble concentrating on things, such as reading the newspaper or watching television | توجہ مرکوز رکھنے میں دشواری، جیسے اخبار پڑھنے یا ٹی وی دیکھنے میں۔",
                    "type": "SCALE",
                    "order": 31,
                    "options": phq_options
                },
                {
                    "content": "[PHQ-9] Moving or speaking so slowly that other people could have noticed — or the opposite, being so fidgety or restless that you have been moving around a lot more than usual | اتنی سست روی سے چلنا یا بولنا کہ دوسروں نے اس کی نشاندہی کی ہو، یا اس کے برعکس معمول سے کہیں زیادہ بے چینی یا اضطراب۔",
                    "type": "SCALE",
                    "order": 32,
                    "options": phq_options
                },
                {
                    "content": "[PHQ-9] Thoughts that you would be better off dead, or of hurting yourself | ذہن میں اس خیال کا بار بار آنا کہ زندہ رہنے سے مر جانا بہتر ہے، یا اپنی ذات کو نقصان پہنچانے کے خیالات۔",
                    "type": "SCALE",
                    "order": 33,
                    "options": phq_options
                },
                # --- GAD-7 questions ---
                # Section header (bilingual, display-only, not scored)
                {
                    "content": "[GAD-7] Over the last 2 weeks, how often have you been bothered by the following problems? | گزشتہ دو ہفتوں کے دوران مندرجہ ذیل مسائل نے آپ کو کتنا پریشان کیا؟",
                    "type": "TEXT",
                    "order": 34,
                    "required": False,
                    "options": []
                },
                # GAD-7 items: orders 35-41
                {
                    "content": "[GAD-7] Feeling nervous, anxious, or on edge | گھبراہٹ، پریشانی یا شدید نوعیت کا تناؤ",
                    "type": "SCALE",
                    "order": 35,
                    "options": phq_options
                },
                {
                    "content": "[GAD-7] Not being able to stop or control worrying | پریشانی یا فکر پر قابو پانے میں دشواری",
                    "type": "SCALE",
                    "order": 36,
                    "options": phq_options
                },
                {
                    "content": "[GAD-7] Worrying too much about different things | مختلف چیزوں کے بارے میں حد سے زیادہ بڑھی ہوئی تشویش",
                    "type": "SCALE",
                    "order": 37,
                    "options": phq_options
                },
                {
                    "content": "[GAD-7] Trouble relaxing | پُرسکون رہنے میں دشواری",
                    "type": "SCALE",
                    "order": 38,
                    "options": phq_options
                },
                {
                    "content": "[GAD-7] Being so restless that it is hard to sit still | اس قدر بے چینی یا اضطراب کہ ایک جگہ بیٹھنا مشکل ہو جائے",
                    "type": "SCALE",
                    "order": 39,
                    "options": phq_options
                },
                {
                    "content": "[GAD-7] Becoming easily annoyed or irritable | معمولی باتوں کا چڑچڑاپن",
                    "type": "SCALE",
                    "order": 40,
                    "options": phq_options
                },
                {
                    "content": "[GAD-7] Feeling afraid, as if something awful might happen | ایک انجانے خوف کا احساس جیسے کچھ بہت برا ہونے والا ہے",
                    "type": "SCALE",
                    "order": 41,
                    "options": phq_options
                },
                # --- PANAS questions ---
                # Section header (bilingual, display-only, not scored)
                {
                    "content": "[PANAS] Indicate the extent you feel this way in general. | لوگ اپنی زندگی میں مختلف قسم کے جذبات محسوس کرتے ہیں۔ آپ مندرجہ ذیل جذبات کس حد تک محسوس کرتے ہیں؟",
                    "type": "TEXT",
                    "order": 42,
                    "required": False,
                    "options": []
                },
                # PANAS items: orders 43-51
                {
                    "content": "[PANAS] Distressed | پریشان حال",
                    "type": "SCALE",
                    "order": 43,
                    "options": panas_options
                },
                {
                    "content": "[PANAS] Scared | ڈرا ہوا",
                    "type": "SCALE",
                    "order": 44,
                    "options": panas_options
                },
                {
                    "content": "[PANAS] Enthusiastic | پُر جوش",
                    "type": "SCALE",
                    "order": 45,
                    "options": panas_options
                },
                {
                    "content": "[PANAS] Alert | چوکنا / ہوشیار",
                    "type": "SCALE",
                    "order": 46,
                    "options": panas_options
                },
                {
                    "content": "[PANAS] Distressed (tormented) | تکلیف دہ حالت میں",
                    "type": "SCALE",
                    "order": 47,
                    "options": panas_options
                },
                {
                    "content": "[PANAS] Nervous | بے چین / مضطرب",
                    "type": "SCALE",
                    "order": 48,
                    "options": panas_options
                },
                {
                    "content": "[PANAS] Determined | پُر عزم",
                    "type": "SCALE",
                    "order": 49,
                    "options": panas_options
                },
                {
                    "content": "[PANAS] Afraid | خوفزدہ",
                    "type": "SCALE",
                    "order": 50,
                    "options": panas_options
                },
                {
                    "content": "[PANAS] Excited | جوشیلا",
                    "type": "SCALE",
                    "order": 51,
                    "options": panas_options
                },
                # --- Gratitude Scale (26 items): orders 52-77 ---
                {
                    "content": "[Gratitude] I have much to be grateful for in my life. | میرے پاس زندگی میں لوگوں کا شکر گزار ہونے کے لیے بہت کچھ ہے۔",
                    "type": "SCALE",
                    "order": 52,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] If I had to make a list of all the things and people I am grateful for, it would be very long. | اگر مجھے ہر اس چیز/لوگوں کی فہرست بنانی پڑے جن کے لیے میں شکر گزار ہوں تو یہ ایک بہت لمبی فہرست ہوگی۔",
                    "type": "SCALE",
                    "order": 53,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] As I grow older, I find myself able to appreciate the people, events, and situations that have been part of my life history. | جیسے جیسے میری عمر بڑھ رہی ہے، میں خود کو ان لوگوں، واقعات اور حالات کی تعریف کرنے کے قابل محسوس کرتا/ کرتی ہوں جو میری زندگی کی تاریخ کا حصہ رہے ہیں۔",
                    "type": "SCALE",
                    "order": 54,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] I am grateful for what my friends have done for me. | میرے دوستوں نے میرے لیے جو کچھ کیا اس کے لیے میں شکر گزار ہوں۔",
                    "type": "SCALE",
                    "order": 55,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] I value the things/people I have because I know I could lose them at any moment. | میں ان چیزوں/لوگوں کی قدر کرتا/کرتی ہوں جو میرے پاس ہیں کیونکہ میں جانتا/جانتی ہوں کہ میں انہیں کسی بھی وقت کھو سکتا/سکتی ہوں۔",
                    "type": "SCALE",
                    "order": 56,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] I acknowledge what other people (parents, teachers, friends, relatives) have done for me. | میں یہ تسلیم کرتا/کرتی ہوں کہ دوسرے لوگوں (والدین، اساتذہ، دوست، احباب) نے میرے لیے کیا کچھ کیا ہے۔",
                    "type": "SCALE",
                    "order": 57,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] I tell others how grateful I am to them. | میں دوسرے لوگوں کو بتاتا/بتاتی ہوں کہ میں ان کا/کی کتنا/کتنی شکر گزار ہوں۔",
                    "type": "SCALE",
                    "order": 58,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] I am satisfied with what I have in life and grateful to people. | میرے پاس زندگی میں جو کچھ ہے اس کے لیے میں مطمئن ہوں اور لوگوں کا/کی شکر گزار ہوں۔",
                    "type": "SCALE",
                    "order": 59,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] I think being grateful to the people around me and appreciating beautiful things is a pleasant act. | میرے خیال میں اپنے ارد گرد کے لوگوں کا شکر گزار ہونا اور خوبصورت چیزوں کی تعریف کرنا ایک خوشگوار عمل ہے۔",
                    "type": "SCALE",
                    "order": 60,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] I thank those who helped me along the way so that I could succeed in life. | میں ان لوگوں کا شکریہ ادا کرتا/کرتی ہوں جنہوں نے راستے میں میری مدد کی تاکہ میں زندگی میں کامیابی حاصل کر سکوں۔",
                    "type": "SCALE",
                    "order": 61,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] I am grateful to those who helped me obtain my basic needs (e.g., food, clothing, shelter). | میں ان لوگوں کا/کی شکر گزار ہوں جنہوں نے مجھے میری بنیادی ضروریات (مثلاً کھانے کے لیے کچھ، پہننے کے لیے کپڑے، رہنے کی جگہ) حاصل کرنے میں مدد کی۔",
                    "type": "SCALE",
                    "order": 62,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] Whenever I meet people (friends, relatives, parents) who have helped me, I thank them. | جب بھی میری ان لوگوں (دوست، احباب، والدین) سے ملاقات ہوتی ہے جنہوں نے میری مدد کی، میں ان کا شکریہ ادا کرتا/کرتی ہوں۔",
                    "type": "SCALE",
                    "order": 63,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] I am grateful for what others have done for me in my life. | میں اپنی زندگی میں دوسروں کی طرف سے میرے لیے کیے گئے کاموں کے لیے شکر گزار ہوں۔",
                    "type": "SCALE",
                    "order": 64,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] I am grateful to the many people who gave me valuable advice or help that brought me to where I am today. | میں بہت سے لوگوں کی/کا شکر گزار ہوں جنہوں نے مجھے قیمتی مشورے یا مدد دی جس سے آج میں جہاں ہوں، وہاں تک پہنچنے میں مدد ملی۔",
                    "type": "SCALE",
                    "order": 65,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] I feel that when I get what I need, God is blessing me. | مجھے لگتا ہے کہ جب مجھے اپنی ضرورت کی چیز ملتی ہے تو خدا مجھے برکت دے رہا ہے۔",
                    "type": "SCALE",
                    "order": 66,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] Experiences of loss have taught me to focus on every moment of life and thank Allah. | نقصان کے تجربات نے مجھے زندگی کے ہر لمحے پر توجہ دینا اور اللہ کا شکر بجا لانا سکھایا ہے۔",
                    "type": "SCALE",
                    "order": 67,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] After meals, I often think, 'What a wonderful meal Allah has provided!' | کھانے کے بعد، میں اکثر سوچتی/سوچتا ہوں، 'کیا شاندار کھانا اللہ نے نصیب کیا ہے!'",
                    "type": "SCALE",
                    "order": 68,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] The thought of death reminds me to live each day to the fullest and to thank Allah. | موت کا خیال مجھے ہر روز ایک بھرپور زندگی گزارنے اور اللہ کا شکر ادا کرنے کی یاد دلاتا ہے۔",
                    "type": "SCALE",
                    "order": 69,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] I often think that life is truly a blessing. | میں اکثر سوچتی/سوچتا ہوں کہ زندگی واقعی ایک نعمت ہے۔",
                    "type": "SCALE",
                    "order": 70,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] I think it is very important to be grateful to Allah every day. | میرے خیال میں ہر روز اللہ کا شکر گزار ہونا بہت ضروری ہے۔",
                    "type": "SCALE",
                    "order": 71,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] Allah has blessed me with many things for which I am grateful to Allah. | اللہ تعالیٰ نے مجھے بہت سی نعمتوں سے نوازا ہے جس پر میں اللہ کا/کی شکر گزار ہوں۔",
                    "type": "SCALE",
                    "order": 72,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] Whenever I achieve any success, I am grateful to Allah for it. | جب بھی میں کوئی کامیابی حاصل کرتی/کرتا ہوں تو اس پر اللہ کی/کا شکر گزار ہوتی/ہوتا ہوں۔",
                    "type": "SCALE",
                    "order": 73,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] Whenever I look at my life, I feel that Allah has shown special grace upon me. | جب بھی میں اپنی زندگی پر نظر ڈالتی/ڈالتا ہوں تو اس چیز کا احساس ہوتا ہے کہ مجھ پر اللہ کا خاص کرم ہے۔",
                    "type": "SCALE",
                    "order": 74,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] I thank Allah for His blessings by offering prayer (namaz). | میں نماز ادا کر کے اللہ کی نعمتوں کا شکر ادا کرتا/کرتی ہوں۔",
                    "type": "SCALE",
                    "order": 75,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] I am grateful to Allah who gave me parents who took care of my needs. | میں اللہ کا/کی شکر گزار ہوں جس نے مجھے میری ضروریات کا خیال رکھنے والے والدین عطا کیے۔",
                    "type": "SCALE",
                    "order": 76,
                    "options": grat_options
                },
                {
                    "content": "[Gratitude] I am grateful to Allah who gave me parents who understand me on every occasion. | میں اللہ کا/کی شکر گزار ہوں جس نے مجھے ایسے والدین عطا کیے جو ہر موقع پر میرا احساس کرتے ہیں۔",
                    "type": "SCALE",
                    "order": 77,
                    "options": grat_options
                },
                # --- SIDAS Scale (5 items) ---
                {
                    "content": "[SIDAS] In the past month, how often have you had thoughts about suicide? | پچھلے ایک مہینے میں آپ کو خودکشی کے خیالات کتنی بار آئے ہیں؟",
                    "type": "SCALE",
                    "order": 78,
                    "options": sidas_options_1
                },
                {
                    "content": "[SIDAS] In the past month, how much control have you had over these thoughts? | پچھلے ایک مہینے میں، آپ کو کتنا محسوس ہوا کہ آپ ان خیالات کو قابو میں رکھ سکتے تھے؟",
                    "type": "SCALE",
                    "order": 79,
                    "options": sidas_options_2
                },
                {
                    "content": "[SIDAS] In the past month, how close have you come to making a suicide attempt? | پچھلے ایک مہینے میں آپ خودکشی کرنے کے کتنے قریب پہنچے تھے؟",
                    "type": "SCALE",
                    "order": 80,
                    "options": sidas_options_3
                },
                {
                    "content": "[SIDAS] In the past month, to what extent have you felt tormented by thoughts about suicide? | پچھلے ایک مہینے میں آپ خودکشی کے خیالات سے کتنا پریشان یا تنگ رہے تھے؟",
                    "type": "SCALE",
                    "order": 81,
                    "options": sidas_options_4_5
                },
                {
                    "content": "[SIDAS] In the past month, how much have thoughts about suicide interfered with your ability to carry out daily activities (work, household tasks, or social activities)? | پچھلے ایک مہینے میں خودکشی کے خیالات نے آپ کی روزمرہ کی سرگرمیوں (کام، گھر کے کام یا سماجی میل جول) میں کتنا خلل ڈالا ہے؟",
                    "type": "SCALE",
                    "order": 82,
                    "options": sidas_options_4_5
                }
            ]
            self._sync_questions_for_questionnaire(battery_q, battery_data)
            self.stdout.write(self.style.SUCCESS(f"All questions synced for '{battery_title}'."))

    def _sync_questions_for_questionnaire(self, questionnaire, data):
        """
        Idempotent sync — creates or updates questions identified by order number.

        Algorithm:
          Pass 1 — move all existing questions to temporary NEGATIVE orders
                   (avoids unique-order conflicts during the reconcile).
          Pass 2 — for each desired question:
                   • if an old question existed at that order, update it in-place
                     (preserving PK and all linked Response rows).
                   • otherwise create a fresh Question.
          Pass 3 — upsert each option by numeric_value (update label; create if new).
        """
        from django.db import transaction

        with transaction.atomic():
            # ── Pass 1: park all existing questions at temp high orders ──────────
            # (avoids unique-order conflicts during the reconcile; uses offset
            #  instead of negative values to satisfy CHECK(order >= 0) constraint)
            TEMP_OFFSET = 10000
            existing = list(questionnaire.questions.order_by("order"))
            existing_by_order = {}
            for q in existing:
                orig_order = q.order
                existing_by_order[orig_order] = q
                q.order = TEMP_OFFSET + orig_order
                q.save(update_fields=["order"])

            # ── Pass 2: upsert each desired question ─────────────────────────
            for q_data in data:
                target_order = q_data["order"]
                content      = q_data["content"]
                q_type       = q_data["type"]
                required     = q_data.get("required", True)
                options      = q_data.get("options", [])

                old_q = existing_by_order.get(target_order)

                if old_q:
                    # Update existing record in-place (keeps PK → Response FKs intact)
                    old_q.order    = target_order
                    old_q.content  = content
                    old_q.type     = q_type
                    old_q.required = required
                    old_q.save(update_fields=["order", "content", "type", "required"])
                    q_obj = old_q
                else:
                    q_obj = Question.objects.create(
                        questionnaire=questionnaire,
                        content=content,
                        type=q_type,
                        order=target_order,
                        required=required,
                    )

                # ── Pass 3: upsert options by numeric_value ──────────────────
                existing_opts = {opt.numeric_value: opt for opt in q_obj.options.all()}
                desired_vals = {opt_val for _, opt_val in options}
                for opt_label, opt_val in options:
                    if opt_val in existing_opts:
                        opt = existing_opts[opt_val]
                        if opt.label != opt_label:
                            opt.label = opt_label
                            opt.save(update_fields=["label"])
                    else:
                        Option.objects.create(
                            question=q_obj,
                            label=opt_label,
                            numeric_value=opt_val,
                            order=opt_val,
                        )

                # ── Pass 3b: prune stale options not in the desired set ───────
                # Stale options arise when a question's scale changes (e.g. 0-10
                # → 0-4 due to order reassignment). Response rows use SET_NULL +
                # cached selected_option_value so scoring survives the deletion.
                for stale_val, stale_opt in existing_opts.items():
                    if stale_val not in desired_vals:
                        stale_opt.delete()


            # Any remaining questions parked at high temp orders are orphans
            # (orders no longer in the desired layout). We leave them rather than
            # deleting, to protect any linked Response data.
            orphans = questionnaire.questions.filter(order__gte=TEMP_OFFSET)
            orphan_count = orphans.count()
            if orphan_count:
                self.stdout.write(self.style.WARNING(
                    f"  {orphan_count} orphaned question(s) left at negative orders "
                    f"(have linked Response data — not deleted)."
                ))
