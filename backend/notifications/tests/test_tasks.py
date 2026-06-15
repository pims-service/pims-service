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
    assert "Day 1 of Phase 1" in sent_email.subject
    assert sent_email.to == [test_user.email]
    assert "Sarah" in sent_email.body
    assert "Sarah" in sent_email.alternatives[0][0]
    assert "Start today's exercise" in sent_email.alternatives[0][0]
    assert "آج کی مشق شروع کریں" in sent_email.alternatives[0][0]

    # 2. Notification without "reflection" in message (milestone/assessment due, should send due email)
    mail.outbox = []
    notif_due = Notification.objects.create(
        user=test_user,
        n_type='email',
        message='Your 7-day post-test assessment is now due.',
        scheduled_time=timezone.now(),
        status='pending'
    )

    res2 = send_notification(notif_due.pk)
    notif_due.refresh_from_db()
    assert notif_due.status == 'sent'
    
    # Assert email was sent
    assert len(mail.outbox) == 1
    sent_email = mail.outbox[0]
    assert sent_email.subject == "PIMS Assessment Due Reminder"
    assert sent_email.to == [test_user.email]
    assert "Sarah Kim" in sent_email.body
    assert "Your 7-day post-test assessment is now due." in sent_email.body
    assert "Assessment Due Reminder" in sent_email.alternatives[0][0]
    assert "Go to Dashboard" in sent_email.alternatives[0][0]

    # 3. Notification without "reflection" in message (milestone/assessment overdue, should send overdue email)
    mail.outbox = []
    notif_overdue = Notification.objects.create(
        user=test_user,
        n_type='email',
        message='Reminder: Your 3-month follow-up assessment is overdue.',
        scheduled_time=timezone.now(),
        status='pending'
    )

    res3 = send_notification(notif_overdue.pk)
    notif_overdue.refresh_from_db()
    assert notif_overdue.status == 'sent'
    
    # Assert email was sent
    assert len(mail.outbox) == 1
    sent_email_od = mail.outbox[0]
    assert sent_email_od.subject == "PIMS Assessment Overdue Reminder"
    assert sent_email_od.to == [test_user.email]
    assert "Sarah Kim" in sent_email_od.body
    assert "Reminder: Your 3-month follow-up assessment is overdue." in sent_email_od.body
    assert "Assessment Overdue Reminder" in sent_email_od.alternatives[0][0]
    assert "Go to Dashboard" in sent_email_od.alternatives[0][0]


@pytest.mark.django_db
def test_send_notification_inactive_user(test_user):
    from notifications.models import Notification
    from notifications.tasks import send_notification
    from django.core import mail

    test_user.is_active = False
    test_user.save()
    mail.outbox = []

    notif = Notification.objects.create(
        user=test_user,
        n_type='email',
        message='Hello',
        scheduled_time=timezone.now(),
        status='pending',
    )

    result = send_notification(notif.pk)
    notif.refresh_from_db()
    assert notif.status == 'failed'
    assert result['status'] == 'failed'
    assert result['reason'] == 'inactive_user'
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_send_notification_missing_email(test_user):
    from notifications.models import Notification
    from notifications.tasks import send_notification
    from django.core import mail

    test_user.email = ""
    test_user.save()
    mail.outbox = []

    notif = Notification.objects.create(
        user=test_user,
        n_type='email',
        message='Hello',
        scheduled_time=timezone.now(),
        status='pending',
    )

    result = send_notification(notif.pk)
    notif.refresh_from_db()
    assert notif.status == 'failed'
    assert result['status'] == 'failed'
    assert result['reason'] == 'missing_email'
    assert len(mail.outbox) == 0
