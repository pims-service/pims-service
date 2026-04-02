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
