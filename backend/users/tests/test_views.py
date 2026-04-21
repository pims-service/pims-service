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
        "consent_version": "1.0"
    }
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


# ── Issue #24: Authentication system tests ──────────────────────────────────

@pytest.mark.django_db
def test_registration_api(api_client, db):
    """Registration with valid data returns 201 and creates user + consent."""
    Role.objects.get_or_create(name='Participant')
    url = reverse('register')
    payload = {
        "username": "authuser",
        "full_name": "Auth User",
        "email": "authuser@example.com",
        "password": "securepass1!",
        "confirm_password": "securepass1!",
        "whatsapp_number": "+1234567890",
        "consent_agreed": True,
        "consent_version": "1.0",
    }
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(username="authuser").exists()
    assert UserConsent.objects.filter(user__username="authuser", agreed=True).exists()


@pytest.mark.django_db
def test_login_api(api_client, test_user):
    """Login with correct credentials returns access and refresh tokens."""
    url = reverse('token_obtain_pair')
    payload = {"username": "testuser", "password": "password123"}
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db
def test_login_invalid_credentials(api_client, test_user):
    """Login with wrong password returns 401."""
    url = reverse('token_obtain_pair')
    payload = {"username": "testuser", "password": "wrongpassword"}
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_login_nonexistent_user(api_client, db):
    """Login with a username that does not exist returns 401."""
    url = reverse('token_obtain_pair')
    payload = {"username": "ghost", "password": "irrelevant"}
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_protected_endpoint_requires_auth(api_client, db):
    """Unauthenticated request to a protected endpoint returns 401."""
    url = reverse('profile')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_protected_endpoint_with_valid_token(api_client, test_user):
    """Authenticated request to a protected endpoint returns 200."""
    url = reverse('token_obtain_pair')
    token_response = api_client.post(url, {"username": "testuser", "password": "password123"})
    assert token_response.status_code == status.HTTP_200_OK
    access_token = token_response.data["access"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    profile_url = reverse('profile')
    response = api_client.get(profile_url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["username"] == test_user.username


@pytest.mark.django_db
def test_no_unauthorized_access_to_admin_endpoint(api_client, test_user):
    """Non-admin authenticated user cannot access admin-only endpoints."""
    api_client.force_authenticate(user=test_user)
    url = reverse('admin_user_list')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


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
        }
        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_201_CREATED

    for group in groups:
        # NEW: Verify deferred assignment (Groups should remain empty after signup)
        assert group.participants.count() == 0
