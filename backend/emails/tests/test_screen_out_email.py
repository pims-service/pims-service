import pytest
from django.core import mail

from emails.builder import build_screen_out_email
from emails.tasks import send_screen_out_email_task, send_welcome_email_task


def test_build_screen_out_email_is_bilingual():
    content = build_screen_out_email(
        'Sara',
        links={
            'withdraw_link': 'https://psycheversity.com/profile',
            'support_page_link': 'https://psycheversity.com',
        },
    )

    assert 'Thank you for your interest' in content['subject']
    assert 'آپ کی دلچسپی کا شکریہ' in content['subject']
    assert 'Dear Sara,' in content['html_content']
    assert 'محترم Sara،' in content['html_content']
    assert 'this self-guided writing program is not the right fit' in content['html_content']
    assert 'یہ خود رہنمائی پر مبنی تحریری پروگرام' in content['html_content']
    assert 'Support &amp; Crisis Resources' in content['html_content']
    assert 'معاونت و بحرانی رابطے' in content['html_content']
    assert 'Umang' in content['html_content']
    assert 'امنگ' in content['html_content']
    assert '0311-7786264' in content['html_content']


@pytest.mark.django_db
def test_send_screen_out_email_task_sends_mail(test_user, settings):
    from questionnaires.models import Questionnaire, ResponseSet

    test_user.full_name = 'Sara Ahmed'
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

    result = send_screen_out_email_task(test_user.user_id)

    assert result['status'] == 'sent'
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == [test_user.email]
    assert 'Thank you for your interest' in message.subject
    assert 'آپ کی دلچسپی کا شکریہ' in message.subject
    html_body = message.alternatives[0][0]
    assert 'not the right fit for you at this time' in html_body


@pytest.mark.django_db
def test_send_screen_out_email_task_skips_without_signup_risk(test_user):
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
        suicide_risk_triggered=False,
    )

    result = send_screen_out_email_task(test_user.user_id)

    assert result['status'] == 'skipped'
    assert result['reason'] == 'no_signup_risk_trigger'
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_disqualified_screen_out_user_does_not_receive_welcome(test_user):
    from questionnaires.models import Questionnaire, ResponseSet

    test_user.is_disqualified = True
    test_user.disqualification_reason = 'Safety screener exclusion at sign-up.'
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

    assert result['status'] == 'skipped'
    assert result['reason'] == 'disqualified'
