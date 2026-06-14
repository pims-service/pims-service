import pytest
from django.core import mail

from emails.builder import build_support_email
from emails.tasks import send_support_email_task, send_welcome_email_task


def test_build_support_email_is_bilingual():
    content = build_support_email(
        'Sara',
        links={
            'withdraw_link': 'https://psycheversity.com/profile',
            'support_page_link': 'https://psycheversity.com',
        },
    )

    assert 'Support resources are available' in content['subject']
    assert 'معاونت کے وسائل دستیاب ہیں' in content['subject']
    assert 'Dear Sara,' in content['html_content']
    assert 'محترم Sara،' in content['html_content']
    assert 'You are not alone' in content['html_content']
    assert 'آپ اکیلے نہیں ہیں' in content['html_content']
    assert 'Support &amp; Crisis Resources' in content['html_content']
    assert 'Umang' in content['html_content']


@pytest.mark.django_db
def test_send_support_email_task_sends_mail(test_user, settings):
    test_user.full_name = 'Sara Ahmed'
    test_user.save()

    result = send_support_email_task(test_user.user_id)

    assert result['status'] == 'sent'
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == [test_user.email]
    assert 'Support resources are available' in message.subject
    assert 'معاونت کے وسائل دستیاب ہیں' in message.subject
    html_body = message.alternatives[0][0]
    assert 'You are not alone' in html_body


@pytest.mark.django_db
def test_send_support_email_task_skips_disqualified_user(test_user):
    test_user.is_disqualified = True
    test_user.save()

    result = send_support_email_task(test_user.user_id)

    assert result['status'] == 'skipped'
    assert result['reason'] == 'disqualified'
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_disqualified_user_does_not_receive_welcome(test_user):
    from questionnaires.models import Questionnaire, ResponseSet

    test_user.is_disqualified = True
    test_user.disqualification_reason = 'Answered YES to eligibility screener.'
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
