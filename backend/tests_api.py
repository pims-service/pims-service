import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User

@pytest.mark.django_db
def test_user_registration():
    client = APIClient()
    url = reverse('register')
    data = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "strongpassword123",
        "whatsapp_number": "+1234567890",
        "email_consent": True,
        "whatsapp_consent": True
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.count() == 1
    user = User.objects.get()
    assert user.username == "newuser"
    assert user.whatsapp_number == "+1234567890"
    assert user.email_consent is True
