import pytest
from django.core import mail

from emails.builder import build_socio_disqualification_email
from emails.tasks import send_socio_disqualification_email_task


def test_build_socio_disqualification_email_is_bilingual():
    content = build_socio_disqualification_email(
        'Sara',
        links={
            'withdraw_link': 'https://psycheversity.com/profile',
            'support_page_link': 'https://psycheversity.com',
        },
    )

    assert 'Thank you for your interest' in content['subject']
    assert 'اہلیت کے بارے میں' in content['subject']
    assert 'Dear Sara,' in content['html_content']
    assert 'not the right fit for you at this time' in content['html_content']
    assert 'موزوں نہیں' in content['html_content']


@pytest.mark.django_db
def test_send_socio_disqualification_email_task_sends_mail(test_user, settings):
    test_user.full_name = 'Sara Ahmed'
    test_user.is_disqualified = True
    test_user.disqualification_reason = 'Answered YES to eligibility screener.'
    test_user.save()

    result = send_socio_disqualification_email_task(test_user.user_id)

    assert result['status'] == 'sent'
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == [test_user.email]
    assert 'Thank you for your interest' in message.subject
    html_body = message.alternatives[0][0]
    assert 'not the right fit for you at this time' in html_body


@pytest.mark.django_db
def test_send_socio_disqualification_email_task_skips_non_disqualified_user(test_user):
    result = send_socio_disqualification_email_task(test_user.user_id)

    assert result['status'] == 'skipped'
    assert result['reason'] == 'not_disqualified'
    assert len(mail.outbox) == 0
