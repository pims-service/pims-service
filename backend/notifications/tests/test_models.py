import pytest
from notifications.models import Notification
from django.utils import timezone

@pytest.mark.django_db
def test_notification_creation(test_user):
    notification = Notification.objects.create(
        user=test_user,
        n_type='email',
        message="Test Message",
        scheduled_time=timezone.now(),
        status='pending'
    )
    assert notification.message == "Test Message"
    assert notification.status == 'pending'
    assert str(notification) == f"{test_user.username} - email - pending"
