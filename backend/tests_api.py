import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User

@pytest.mark.django_db
def test_user_registration():
    from users.models import EmailVerificationOTP
    client = APIClient()
    url = reverse('register')
    data = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "strongpassword123",
        "confirm_password": "strongpassword123",
        "whatsapp_number": "+1234567890",
        "consent_agreed": True,
        "consent_version": "1.0",
        "otp": "123456"
    }
    EmailVerificationOTP.objects.create(email="new@example.com", otp="123456")
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.count() == 1
    user = User.objects.get()
    assert user.username == "newuser"
    assert user.whatsapp_number == "+1234567890"

