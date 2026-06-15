import pytest
from django.core import mail

from emails.builder import build_otp_email, build_password_reset_email
from users.tasks import send_otp_email_task, send_password_reset_email_task


def test_build_otp_email_is_bilingual():
    content = build_otp_email('123456')

    # Subject checks
    assert 'Your Email Verification Code' in content['subject']
    assert 'آپ کا ای میل تصدیقی کوڈ' in content['subject']

    # HTML body checks
    assert '123456' in content['html_content']
    assert 'Email Verification' in content['html_content']
    assert 'ای میل کی تصدیق' in content['html_content']
    assert 'Welcome to Psycheversity' in content['html_content']
    assert 'سائیکیورسٹی میں خوش آمدید' in content['html_content']
    assert 'Noto Nastaliq Urdu' in content['html_content']
    assert 'dir="rtl"' in content['html_content']

    # Text body checks
    assert '123456' in content['text_content']
    assert 'Your Email Verification Code' in content['text_content']
    assert 'آپ کا ای میل تصدیقی کوڈ' in content['text_content']


def test_build_password_reset_email_is_bilingual():
    content = build_password_reset_email('Sara', '987654')

    # Subject checks
    assert 'PIMS Password Reset Request' in content['subject']
    assert 'پاس ورڈ دوبارہ ترتیب دینے کی درخواست' in content['subject']

    # HTML body checks
    assert '987654' in content['html_content']
    assert 'Dear Sara,' in content['html_content']
    assert 'محترم Sara،' in content['html_content']
    assert 'Password Reset Verification' in content['html_content']
    assert 'پاس ورڈ دوبارہ ترتیب دینے کی تصدیق' in content['html_content']
    assert 'Noto Nastaliq Urdu' in content['html_content']
    assert 'dir="rtl"' in content['html_content']

    # Text body checks
    assert '987654' in content['text_content']
    assert 'PIMS Password Reset Request' in content['text_content']
    assert 'پاس ورڈ دوبارہ ترتیب دینے کی درخواست' in content['text_content']


@pytest.mark.django_db
def test_send_otp_email_task_sends_bilingual_email():
    mail.outbox.clear()
    
    result = send_otp_email_task('otp_recipient@example.com', '123456')
    assert result is True
    assert len(mail.outbox) == 1
    
    message = mail.outbox[0]
    assert message.to == ['otp_recipient@example.com']
    assert 'Your Email Verification Code' in message.subject
    assert 'آپ کا ای میل تصدیقی کوڈ' in message.subject
    
    # HTML alternative check
    assert len(message.alternatives) == 1
    html_body = message.alternatives[0][0]
    assert '123456' in html_body
    assert 'Welcome to Psycheversity' in html_body
    assert 'سائیکیورسٹی میں خوش آمدید' in html_body


@pytest.mark.django_db
def test_send_password_reset_email_task_sends_bilingual_email():
    mail.outbox.clear()
    
    result = send_password_reset_email_task('reset_recipient@example.com', 'Sara', '987654')
    assert result is True
    assert len(mail.outbox) == 1
    
    message = mail.outbox[0]
    assert message.to == ['reset_recipient@example.com']
    assert 'PIMS Password Reset Request' in message.subject
    assert 'پاس ورڈ دوبارہ ترتیب دینے کی درخواست' in message.subject
    
    # HTML alternative check
    assert len(message.alternatives) == 1
    html_body = message.alternatives[0][0]
    assert '987654' in html_body
    assert 'Dear Sara,' in html_body
    assert 'محترم Sara،' in html_body
