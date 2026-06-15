"""E3–E12 booster / phase email copy from Psycheversity_Participant_Emails_Bilingual.docx."""

DAILY_NUDGE_EMAIL = {
    'subject_en': "Day {day_in_phase} of Phase {phase} : today's writing exercise",
    'subject_ur': 'مرحلہ {phase} کا دن {day_in_phase} : آج کی تحریری مشق',
    'title_en': "Today's Writing Exercise",
    'title_ur': 'آج کی تحریری مشق',
    'lead_en': (
        'Dear {first_name}, here is Day {day_in_phase} of Phase {phase}. '
        "Tap below to complete today's short writing exercise."
    ),
    'lead_ur': (
        'محترم {first_name}، یہ مرحلہ {phase} کا دن {day_in_phase} ہے۔ '
        'آج کی مختصر تحریری مشق مکمل کرنے کے لیے نیچے دبائیں۔'
    ),
    'button_en': "Start today's exercise",
    'button_ur': 'آج کی مشق شروع کریں',
}

PHASE_1_COMPLETE_EMAIL = {
    'subject_en': 'Phase 1 complete : thank you',
    'subject_ur': 'مرحلہ 1 مکمل : شکریہ',
    'title_en': 'Phase 1 Complete',
    'title_ur': 'مرحلہ 1 مکمل',
    'paragraphs_en': [
        'You have completed Phase 1. Thank you for your effort over these seven days.',
        (
            'There is now a short break. We will contact you again before the end of the month '
            'to begin the next phase.'
        ),
        'Nothing is needed from you until then.',
    ],
    'paragraphs_ur': [
        'آپ نے مرحلہ 1 مکمل کر لیا ہے۔ ان سات دنوں میں آپ کی محنت کا شکریہ۔',
        'اب ایک مختصر وقفہ ہے۔ اگلے مرحلے کے لیے ہم مہینے کے اختتام سے پہلے دوبارہ رابطہ کریں گے۔',
        'تب تک آپ سے کسی چیز کی ضرورت نہیں۔',
    ],
    'closing_en': 'Warm regards,',
    'closing_team_en': 'Psycheversity Research Team',
    'closing_ur': 'نیک تمناؤں کے ساتھ،',
    'closing_team_ur': 'سائیکیورسٹی ریسرچ ٹیم',
}

PHASE_2_COMPLETE_EMAIL = {
    'subject_en': 'Phase 2 complete : thank you',
    'subject_ur': 'مرحلہ 2 مکمل : شکریہ',
    'title_en': 'Phase 2 Complete',
    'title_ur': 'مرحلہ 2 مکمل',
    'paragraphs_en': [
        'You have completed Phase 2. Thank you for staying with the study.',
        'There is now a longer break before the next phase. We will contact you again when it is time to continue.',
    ],
    'paragraphs_ur': [
        'آپ نے مرحلہ 2 مکمل کر لیا ہے۔ تحقیق کے ساتھ جُڑے رہنے کا شکریہ۔',
        'اگلے مرحلے سے پہلے اب ایک قدرے طویل وقفہ ہے۔ جب جاری رکھنے کا وقت ہوگا تو ہم دوبارہ رابطہ کریں گے۔',
    ],
    'closing_en': 'Warm regards,',
    'closing_team_en': 'Psycheversity Research Team',
    'closing_ur': 'نیک تمناؤں کے ساتھ،',
    'closing_team_ur': 'سائیکیورسٹی ریسرچ ٹیم',
}

PHASE_INVITE_TEMPLATES = {
    'phase_2': {
        'subject_en': 'Your next phase starts soon',
        'subject_ur': 'آپ کا اگلا مرحلہ جلد شروع ہو رہا ہے',
        'title_en': 'Your Next Phase Starts Soon',
        'title_ur': 'آپ کا اگلا مرحلہ جلد شروع ہو رہا ہے',
        'paragraphs_en': [
            'Your next phase is about to begin. In a few days you will restart the seven-day writing exercise.',
            (
                'These short sessions are the heart of the study, and your steady participation makes the '
                'findings meaningful. We hope you will continue with us.'
            ),
            'We will send your daily link once the phase begins.',
        ],
        'paragraphs_ur': [
            'آپ کا اگلا مرحلہ جلد شروع ہونے والا ہے۔ چند دنوں میں آپ سات روزہ تحریری مشق دوبارہ شروع کریں گے۔',
            (
                'یہ مختصر نشستیں اس تحقیق کا اصل حصہ ہیں، اور آپ کی مسلسل شرکت نتائج کو بامعنی بناتی ہے۔ '
                'ہمیں اُمید ہے کہ آپ ہمارے ساتھ جاری رکھیں گے۔'
            ),
            'مرحلہ شروع ہوتے ہی ہم آپ کو روزانہ کا لنک بھیجیں گے۔',
        ],
    },
    'phase_3': {
        'subject_en': 'Your next phase starts soon',
        'subject_ur': 'آپ کا اگلا مرحلہ جلد شروع ہو رہا ہے',
        'title_en': 'Your Next Phase Starts Soon',
        'title_ur': 'آپ کا اگلا مرحلہ جلد شروع ہو رہا ہے',
        'paragraphs_en': [
            'Your next phase begins in a few days, with another seven-day writing exercise.',
            (
                'After you finish this phase, you will receive an updated personal wellbeing summary. '
                'We hope you will continue with us.'
            ),
            'We will send your daily link once the phase begins.',
        ],
        'paragraphs_ur': [
            'آپ کا اگلا مرحلہ چند دنوں میں شروع ہوگا، ایک اور سات روزہ تحریری مشق کے ساتھ۔',
            'اس مرحلے کے اختتام پر آپ کو ایک تازہ ذاتی بہبود رپورٹ موصول ہوگی۔ ہمیں اُمید ہے کہ آپ ہمارے ساتھ جاری رکھیں گے۔',
            'مرحلہ شروع ہوتے ہی ہم آپ کو روزانہ کا لنک بھیجیں گے۔',
        ],
    },
    'phase_4': {
        'subject_en': 'Your next phase starts soon',
        'subject_ur': 'آپ کا اگلا مرحلہ جلد شروع ہو رہا ہے',
        'title_en': 'Your Next Phase Starts Soon',
        'title_ur': 'آپ کا اگلا مرحلہ جلد شروع ہو رہا ہے',
        'paragraphs_en': [
            'Your next phase begins in a few days, with another seven-day writing exercise.',
            (
                'After you finish, you will receive an updated personal wellbeing summary. '
                'We are grateful you have stayed with the study this long.'
            ),
            'We will send your daily link once the phase begins.',
        ],
        'paragraphs_ur': [
            'آپ کا اگلا مرحلہ چند دنوں میں شروع ہوگا، ایک اور سات روزہ تحریری مشق کے ساتھ۔',
            'اس کے اختتام پر آپ کو ایک تازہ ذاتی بہبود رپورٹ موصول ہوگی۔ ہم شکر گزار ہیں کہ آپ اتنے عرصے سے ہمارے ساتھ ہیں۔',
            'مرحلہ شروع ہوتے ہی ہم آپ کو روزانہ کا لنک بھیجیں گے۔',
        ],
    },
    'final': {
        'subject_en': 'Your final phase starts soon',
        'subject_ur': 'آپ کا آخری مرحلہ جلد شروع ہو رہا ہے',
        'title_en': 'Your Final Phase Starts Soon',
        'title_ur': 'آپ کا آخری مرحلہ جلد شروع ہو رہا ہے',
        'paragraphs_en': [
            'Your final phase of the study begins in a few days, with one last seven-day writing exercise.',
            (
                'After you complete it, you will receive your final personal wellbeing summary and a '
                'certificate of completion. Thank you for staying with the study all the way to this point.'
            ),
            'We will send your daily link once the phase begins.',
        ],
        'paragraphs_ur': [
            'تحقیق کا آپ کا آخری مرحلہ چند دنوں میں شروع ہوگا، آخری سات روزہ تحریری مشق کے ساتھ۔',
            (
                'اسے مکمل کرنے کے بعد آپ کو اپنی آخری ذاتی بہبود رپورٹ اور تکمیل کا سرٹیفکیٹ موصول ہوگا۔ '
                'آخر تک ہمارے ساتھ رہنے کا شکریہ۔'
            ),
            'مرحلہ شروع ہوتے ہی ہم آپ کو روزانہ کا لنک بھیجیں گے۔',
        ],
    },
}

PHASE_REPORT_COMPLETE_EMAIL = {
    'phase_3_report': {
        'subject_en': 'Phase complete : your updated wellbeing summary',
        'subject_ur': 'مرحلہ مکمل : آپ کی تازہ بہبود رپورٹ',
        'title_en': 'Phase Complete',
        'title_ur': 'مرحلہ مکمل',
        'paragraphs_en': [
            'You have completed this phase. Thank you for your continued participation.',
            (
                'Your updated personal wellbeing summary (PERMA Profiler) is attached as a PDF. As before, '
                'it is a snapshot for your own reflection, not a clinical or diagnostic assessment, and small '
                'changes over time are normal and can be influenced by many factors.'
            ),
            'Please wait for our next message, when the following phase will begin.',
        ],
        'paragraphs_ur': [
            'آپ نے یہ مرحلہ مکمل کر لیا ہے۔ آپ کی مسلسل شرکت کا شکریہ۔',
            (
                'آپ کی تازہ ذاتی بہبود رپورٹ (PERMA پروفائلر) بطور PDF منسلک ہے۔ پہلے کی طرح، '
                'یہ صرف آپ کے غور و فکر کے لیے ایک جھلک ہے، کوئی طبی یا تشخیصی جائزہ نہیں، '
                'اور وقت کے ساتھ معمولی تبدیلیاں فطری ہیں اور کئی عوامل سے متاثر ہو سکتی ہیں۔'
            ),
            'براہِ کرم ہمارے اگلے پیغام کا انتظار کیجیے، جب اگلا مرحلہ شروع ہوگا۔',
        ],
        'closing_en': 'Warm regards,',
        'closing_team_en': 'Psycheversity Research Team',
        'closing_ur': 'نیک تمناؤں کے ساتھ،',
        'closing_team_ur': 'سائیکیورسٹی ریسرچ ٹیم',
    },
    'phase_4_report': {
        'subject_en': 'Phase complete : your updated wellbeing summary',
        'subject_ur': 'مرحلہ مکمل : آپ کی تازہ بہبود رپورٹ',
        'title_en': 'Phase Complete',
        'title_ur': 'مرحلہ مکمل',
        'paragraphs_en': [
            'You have completed this phase. Thank you for your continued participation.',
            (
                'Your updated personal wellbeing summary (PERMA Profiler) is attached as a PDF. As before, '
                'it is a snapshot for your own reflection, not a clinical or diagnostic assessment, and changes '
                'over time can be influenced by many factors.'
            ),
            'Please wait for our next message, when the final phase will begin.',
        ],
        'paragraphs_ur': [
            'آپ نے یہ مرحلہ مکمل کر لیا ہے۔ آپ کی مسلسل شرکت کا شکریہ۔',
            (
                'آپ کی تازہ ذاتی بہبود رپورٹ (PERMA پروفائلر) بطور PDF منسلک ہے۔ پہلے کی طرح، '
                'یہ صرف آپ کے غور و فکر کے لیے ایک جھلک ہے، کوئی طبی یا تشخیصی جائزہ نہیں، '
                'اور وقت کے ساتھ تبدیلیاں کئی عوامل سے متاثر ہو سکتی ہیں۔'
            ),
            'براہِ کرم ہمارے اگلے پیغام کا انتظار کیجیے، جب آخری مرحلہ شروع ہوگا۔',
        ],
        'closing_en': 'Warm regards,',
        'closing_team_en': 'Psycheversity Research Team',
        'closing_ur': 'نیک تمناؤں کے ساتھ،',
        'closing_team_ur': 'سائیکیورسٹی ریسرچ ٹیم',
    },
    'study_complete': {
        'subject_en': 'Study complete : your summary and certificate',
        'subject_ur': 'تحقیق مکمل : آپ کی رپورٹ اور سرٹیفکیٹ',
        'title_en': 'Study Complete',
        'title_ur': 'تحقیق مکمل',
        'paragraphs_en': [
            'Congratulations on completing the Psycheversity Wellbeing Study, including all booster writing exercises, over a twelve-month period.',
            (
                'Attached you will find your final personal wellbeing summary (PERMA Profiler) and your '
                'certificate of completion.'
            ),
            (
                'Thank you for your dedication and for helping advance wellbeing research. '
                'We are deeply grateful for your participation.'
            ),
        ],
        'paragraphs_ur': [
            'سائیکیورسٹی wellbeing تحقیق مکمل کرنے پر مبارک ہو، بشمول تمام booster تحریری مشقیں، بارہ ماہ کے دوران۔',
            'منسلک فائلوں میں آپ کی آخری ذاتی wellbeing رپورٹ (PERMA Profiler) اور تکمیل کا سرٹیفکیٹ شامل ہے۔',
            'آپ کی لگن اور wellbeing تحقیق کو آگے بڑھانے میں مدد کرنے کا شکریہ۔ ہم آپ کی شرکت کے بہت ممنون ہیں۔',
        ],
        'closing_en': 'Warm regards,',
        'closing_team_en': 'Psycheversity Research Team',
        'closing_ur': 'نیک تمناؤں کے ساتھ،',
        'closing_team_ur': 'سائیکیورسٹی ریسرچ ٹیم',
    },
}

EVENING_REMINDER_EMAIL = {
    'subject_en': "Evening Reminder: Day {day_in_phase} of Phase {phase} writing exercise",
    'subject_ur': 'شام کی یاد دہانی: مرحلہ {phase} کے دن {day_in_phase} کی تحریری مشق',
    'title_en': "Evening Reminder",
    'title_ur': 'شام کی یاد دہانی',
    'lead_en': (
        "Dear {first_name}, you haven't completed today's writing exercise (Day {day_in_phase} of Phase {phase}) yet. "
        "There is still time to write before the day ends!"
    ),
    'lead_ur': (
        "محترم {first_name}، آپ نے ابھی تک آج کی تحریری مشق (مرحلہ {phase} کا دن {day_in_phase}) مکمل نہیں کی۔ "
        "دن ختم ہونے سے پہلے ابھی وقت باقی ہے!"
    ),
    'button_en': "Complete today's exercise",
    'button_ur': 'آج کی مشق مکمل کریں',
}

CONSECUTIVE_MISSES_EMAIL = {
    'subject_en': "Let's get back on track with Phase {phase} writing exercises",
    'subject_ur': 'آئیے مرحلہ {phase} کی تحریری مشقیں دوبارہ شروع کریں',
    'title_en': "Let's Get Back on Track",
    'title_ur': 'آئیے دوبارہ شروعات کریں',
    'lead_en': (
        "Dear {first_name}, we noticed you missed your daily reflections for a couple of days. "
        "Research shows consistency is key to benefit from the intervention. Let's get back on track today with Day {day_in_phase} of Phase {phase}!"
    ),
    'lead_ur': (
        "محترم {first_name}، ہم نے محسوس کیا کہ آپ گزشتہ چند دنوں سے اپنی تحریری مشق نہیں کر سکے۔ "
        "تحقیق سے معلوم ہوا ہے کہ اس پروگرام سے پورا فائدہ اٹھانے کے لیے باقاعدگی ضروری ہے۔ آئیے آج سے مرحلہ {phase} کے دن {day_in_phase} کی مشق کے ساتھ دوبارہ شروعات کریں!"
    ),
    'button_en': "Resume your writing",
    'button_ur': 'اپنی تحریر دوبارہ شروع کریں',
}
