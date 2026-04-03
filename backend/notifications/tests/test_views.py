import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
def test_notification_list(authenticated_client, test_user):
    from notifications.models import Notification
    from django.utils import timezone
    Notification.objects.create(
        user=test_user,
        n_type='email',
        message="Test Message",
        scheduled_time=timezone.now()
    )
    url = reverse('notification_list')
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1

@pytest.mark.django_db
def test_admin_schedule_notification(admin_client, test_user):
    from django.utils import timezone
    url = reverse('admin_schedule')
    data = {
        "user": test_user.pk,
        "n_type": "whatsapp",
        "message": "Hello via WhatsApp",
        "scheduled_time": timezone.now().isoformat()
    }
    response = admin_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
