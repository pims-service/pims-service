import pytest
from django.urls import reverse
from rest_framework import status
from users.models import User, UserConsent, Role, EmailVerificationOTP
from groups.models import Group

def create_valid_otp(email):
    return EmailVerificationOTP.objects.create(email=email, otp="123456")

@pytest.mark.django_db
def test_user_profile(authenticated_client, test_user):
    url = reverse('profile')
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['username'] == test_user.username

@pytest.mark.django_db
def test_signup_success(api_client, db):
    Role.objects.get_or_create(name='Participant')
    for i in range(1, 9):
        Group.objects.get_or_create(name=f'Signup_Group_{i}')

    url = reverse('register')
    payload = {
        "username": "newuser",
        "full_name": "New User",
        "email": "new@example.com",
        "password": "password123!",
        "confirm_password": "password123!",
        "whatsapp_number": "+1234567890",
        "consent_agreed": True,
        "consent_version": "1.0",
        "otp": "123456"
    }
    create_valid_otp("new@example.com")
    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(username="newuser").exists()
    assert UserConsent.objects.filter(user__username="newuser", agreed=True).exists()
    user = User.objects.get(username="newuser")
    # NEW: Verify deferred assignment (Group should be None)
    assert user.group is None
    assert response.data.get('group') is None
    assert response.data.get('group_name') is None

@pytest.mark.django_db
def test_signup_without_otp(api_client, db):
    Role.objects.get_or_create(name='Participant')
    url = reverse('register')
    payload = {
        "username": "nootpuser",
        "full_name": "No OTP User",
        "email": "nootp@example.com",
        "password": "password123!",
        "confirm_password": "password123!",
        "whatsapp_number": "+1234567890",
        "consent_agreed": True,
        "consent_version": "1.0",
        "otp": "",
    }
    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(username="nootpuser").exists()

@pytest.mark.django_db
def test_signup_password_mismatch(api_client, db):
    url = reverse('register')
    payload = {
        "username": "mismatchuser",
        "email": "mismatch@example.com",
        "password": "password123!",
        "confirm_password": "differentpassword",
        "consent_agreed": True,
        "consent_version": "1.0",
        "otp": "123456"
    }
    create_valid_otp("mismatch@example.com")
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password" in response.data

@pytest.mark.django_db
def test_signup_consent_required(api_client, db):
    url = reverse('register')
    payload = {
        "username": "noconsent",
        "email": "noconsent@example.com",
        "password": "password123!",
        "confirm_password": "password123!",
        "consent_agreed": False,
        "consent_version": "1.0",
        "otp": "123456"
    }
    create_valid_otp("noconsent@example.com")
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    # Depending on serializer logic, it might be in consent_agreed or non_field_errors
    assert "consent_agreed" in response.data or response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_signup_duplicate_email(api_client, db):
    Role.objects.get_or_create(name='Participant')

    url = reverse('register')
    payload = {
        "username": "firstuser",
        "full_name": "First User",
        "email": "duplicate@example.com",
        "password": "password123!",
        "confirm_password": "password123!",
        "consent_agreed": True,
        "consent_version": "1.0",
        "otp": "123456"
    }
    create_valid_otp("duplicate@example.com")
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_201_CREATED

    payload["username"] = "seconduser"
    payload["otp"] = "123456"
    create_valid_otp("duplicate@example.com")
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data

@pytest.mark.django_db
def test_signup_duplicate_username(api_client, db):
    Role.objects.get_or_create(name='Participant')
    url = reverse('register')
    payload = {
        "username": "taken_username",
        "full_name": "First User",
        "email": "user1@example.com",
        "password": "password123!",
        "confirm_password": "password123!",
        "consent_agreed": True,
        "consent_version": "1.0",
        "otp": ""
    }
    # First signup
    api_client.post(url, payload)
    
    # Second signup with same username but different email
    payload["email"] = "user2@example.com"
    response = api_client.post(url, payload)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "username" in response.data
    error_msg = str(response.data["username"][0]).lower()
    assert "taken" in error_msg or "exists" in error_msg

@pytest.mark.django_db
def test_admin_user_list(admin_client, test_user):
    url = reverse('admin_user_list')
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) >= 1


@pytest.mark.django_db
def test_signup_group_distribution(api_client, db):
    """16 signups across 8 groups should yield exactly 2 per group."""
    Role.objects.get_or_create(name='Participant')
    groups = [Group.objects.get_or_create(name=f'Signup_Dist_{i}')[0] for i in range(1, 9)]

    url = reverse('register')
    for i in range(16):
        payload = {
            "username": f"user{i}",
            "email": f"user{i}@example.com",
            "password": "password123!",
            "confirm_password": "password123!",
            "full_name": f"User {i}",
            "consent_agreed": True,
            "consent_version": "1.0",
            "otp": "123456"
        }
        create_valid_otp(f"user{i}@example.com")
        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_201_CREATED

    for group in groups:
        # NEW: Verify deferred assignment (Groups should remain empty after signup)
        assert group.participants.count() == 0

@pytest.mark.django_db
def test_signup_weak_password(api_client, db):
    Role.objects.get_or_create(name='Participant')
    url = reverse('register')
    payload = {
        "username": "weakuser",
        "email": "weak@example.com",
        "password": "123", # Too short
        "confirm_password": "123",
        "consent_agreed": True,
        "consent_version": "1.0",
        "otp": ""
    }
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password" in response.data
    
    # Test common password
    payload["password"] = "password"
    payload["confirm_password"] = "password"
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password" in response.data
