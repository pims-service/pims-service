import pytest
from django.core import mail

from emails.builder import build_welcome_email, get_first_name
from emails.tasks import send_welcome_email_task


@pytest.mark.django_db
def test_get_first_name_prefers_full_name():
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.create_user(
        username='ali.khan',
        email='ali@example.com',
        password='password123',
        full_name='Ali Khan',
    )
    assert get_first_name(user) == 'Ali'


def test_build_welcome_email_is_bilingual():
    content = build_welcome_email(
        'Sara',
        links={
            'withdraw_link': 'https://psycheversity.com/profile',
            'support_page_link': 'https://psycheversity.com',
        },
    )

    assert 'Welcome to Psycheversity' in content['subject']
    assert 'سائیکیورسٹی میں خوش آمدید' in content['subject']
    assert 'Dear Sara,' in content['html_content']
    assert 'محترم Sara،' in content['html_content']
    assert 'Thank you for joining the Psycheversity wellbeing study' in content['html_content']
    assert 'سائیکیورسٹی کی بہبود تحقیق میں شامل ہونے کا شکریہ' in content['html_content']
    assert 'You can withdraw from this study at any time' in content['html_content']
    assert 'آپ کسی بھی وقت، بغیر کسی نقصان کے' in content['html_content']
    assert 'Noto Nastaliq Urdu' in content['html_content']
    assert 'dir="rtl"' in content['html_content']


@pytest.mark.django_db
def test_send_welcome_email_task_sends_mail(test_user, settings):
    from django.contrib.auth import get_user_model
    from groups.models import Group
    from questionnaires.models import Questionnaire, ResponseSet

    User = get_user_model()
    test_user.full_name = 'Sara Ahmed'
    test_user.has_completed_sociodemographic = True
    test_user.onboarding_completed_at = test_user.created_at
    test_user.group = Group.objects.first()
    test_user.save()

    questionnaire = Questionnaire.objects.create(
        title='Baseline Battery',
        assessment_type='PSYCHOMETRIC',
        is_active=True,
    )
    ResponseSet.objects.create(
        user=test_user,
        questionnaire=questionnaire,
        milestone='SIGNUP',
        status='COMPLETED',
    )

    result = send_welcome_email_task(test_user.user_id)

    assert result['status'] == 'sent'
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == [test_user.email]
    assert message.reply_to == [settings.PARTICIPANT_EMAIL_REPLY_TO]
    assert 'Psycheversity Research Team' in message.from_email
    assert 'Welcome to Psycheversity' in message.subject
    assert 'سائیکیورسٹی میں خوش آمدید' in message.subject
    assert len(message.alternatives) == 1
    html_body = message.alternatives[0][0]
    assert 'Dear Sara,' in html_body
    assert 'محترم Sara،' in html_body


@pytest.mark.django_db
def test_send_welcome_email_task_skips_disqualified_user(test_user):
    from questionnaires.models import Questionnaire, ResponseSet

    test_user.is_disqualified = True
    test_user.onboarding_completed_at = test_user.created_at
    test_user.save()

    questionnaire = Questionnaire.objects.create(
        title='Baseline Battery',
        assessment_type='PSYCHOMETRIC',
        is_active=True,
    )
    ResponseSet.objects.create(
        user=test_user,
        questionnaire=questionnaire,
        milestone='SIGNUP',
        status='COMPLETED',
    )

    result = send_welcome_email_task(test_user.user_id)

    assert result['status'] == 'skipped'
    assert result['reason'] == 'disqualified'
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_send_welcome_email_task_sends_even_with_risk(test_user):
    from questionnaires.models import Questionnaire, ResponseSet

    test_user.onboarding_completed_at = test_user.created_at
    test_user.save()

    questionnaire = Questionnaire.objects.create(
        title='Baseline Battery',
        assessment_type='PSYCHOMETRIC',
        is_active=True,
    )
    ResponseSet.objects.create(
        user=test_user,
        questionnaire=questionnaire,
        milestone='SIGNUP',
        status='COMPLETED',
        suicide_risk_triggered=True,
    )

    result = send_welcome_email_task(test_user.user_id)

    assert result['status'] == 'sent'
    assert len(mail.outbox) == 1
