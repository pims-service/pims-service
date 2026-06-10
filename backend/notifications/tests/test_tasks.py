import pytest
from unittest.mock import patch
from django.utils import timezone


@pytest.mark.django_db
def test_send_notification_marks_sent(test_user):
    from notifications.models import Notification
    from notifications.tasks import send_notification

    notification = Notification.objects.create(
        user=test_user,
        n_type='email',
        message='Hello',
        scheduled_time=timezone.now(),
        status='pending',
    )

    result = send_notification(notification.pk)

    notification.refresh_from_db()
    assert notification.status == 'sent'
    assert result == {'status': 'sent', 'notification_id': notification.pk}


@pytest.mark.django_db
def test_send_notification_not_found():
    from notifications.tasks import send_notification
    from notifications.models import Notification

    with pytest.raises(Notification.DoesNotExist):
        send_notification(99999)


@pytest.mark.django_db
def test_send_notification_task_is_shared_task():
    from notifications.tasks import send_notification
    from celery import Task

    assert isinstance(send_notification, Task)


@pytest.mark.django_db
def test_send_daily_reflection_email_personalization(test_user):
    from django.core import mail
    from notifications.models import Notification
    from notifications.tasks import send_notification

    # Set user full name
    test_user.full_name = "Sarah Kim"
    test_user.save()

    # Clear outbox
    mail.outbox = []

    # 1. Notification with "reflection" in message (should send personalized email)
    notif_reflection = Notification.objects.create(
        user=test_user,
        n_type='email',
        message='Don\'t forget to complete your daily reflection today.',
        scheduled_time=timezone.now(),
        status='pending'
    )

    res1 = send_notification(notif_reflection.pk)
    notif_reflection.refresh_from_db()
    assert notif_reflection.status == 'sent'
    assert res1 == {'status': 'sent', 'notification_id': notif_reflection.pk}
    
    # Assert email was sent
    assert len(mail.outbox) == 1
    sent_email = mail.outbox[0]
    assert sent_email.subject == "PIMS Daily Activity Reminder"
    assert sent_email.to == [test_user.email]
    assert "Sarah Kim" in sent_email.body
    assert "Sarah Kim" in sent_email.alternatives[0][0]
    assert "complete your daily reflection today." in sent_email.body
    assert "Complete Today's Reflection" in sent_email.alternatives[0][0]

    # 2. Notification without "reflection" in message (milestone, should not send email for now)
    mail.outbox = []
    notif_other = Notification.objects.create(
        user=test_user,
        n_type='email',
        message='Your 7-day posttest assessment is now due.',
        scheduled_time=timezone.now(),
        status='pending'
    )

    res2 = send_notification(notif_other.pk)
    notif_other.refresh_from_db()
    assert notif_other.status == 'sent'
    
    # Assert NO email was sent
    assert len(mail.outbox) == 0
