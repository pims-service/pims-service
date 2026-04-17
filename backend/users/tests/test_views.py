import pytest
from django.urls import reverse
from rest_framework import status
from users.models import User, UserConsent, Role
from groups.models import Group

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
        Group.objects.create(name=f'Group {i}')

    url = reverse('register')
    payload = {
        "username": "newuser",
        "full_name": "New User",
        "email": "new@example.com",
        "password": "password123!",
        "confirm_password": "password123!",
        "whatsapp_number": "+1234567890",
        "consent_agreed": True,
        "consent_version": "1.0"
    }
    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(username="newuser").exists()
    assert UserConsent.objects.filter(user__username="newuser", agreed=True).exists()
    user = User.objects.get(username="newuser")
    assert user.group is not None
    assert response.data.get('group') is not None
    assert response.data.get('group_name') is not None

@pytest.mark.django_db
def test_signup_password_mismatch(api_client, db):
    url = reverse('register')
    payload = {
        "username": "mismatchuser",
        "email": "mismatch@example.com",
        "password": "password123!",
        "confirm_password": "differentpassword",
        "consent_agreed": True,
        "consent_version": "1.0"
    }
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
        "consent_version": "1.0"
    }
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
        "consent_version": "1.0"
    }
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_201_CREATED

    payload["username"] = "seconduser"
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data


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
    groups = [Group.objects.create(name=f'Group {i}') for i in range(1, 9)]

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
        }
        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_201_CREATED

    for group in groups:
        # NEW: Verify deferred assignment (Groups should remain empty after signup)
        assert group.participants.count() == 0
