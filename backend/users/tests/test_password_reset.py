import pytest
from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from users.models import User, PasswordResetOTP

@pytest.mark.django_db
@patch('users.tasks.send_password_reset_email_task.delay')
def test_forgot_password_request_success(mock_send_email, api_client, test_user):
    url = reverse('forgot_password_request')
    payload = {"email": test_user.email}
    
    response = api_client.post(url, payload)
    
    assert response.status_code == status.HTTP_200_OK
    assert "code has been sent" in response.data['message']
    
    # Assert OTP record was created in the database
    otp_record = PasswordResetOTP.objects.filter(user=test_user).first()
    assert otp_record is not None
    assert len(otp_record.otp) == 6
    assert otp_record.is_used is False
    
    # Assert email sending task was triggered
    mock_send_email.assert_called_once_with(test_user.email, test_user.display_name, otp_record.otp)


@pytest.mark.django_db
@patch('users.tasks.send_password_reset_email_task.delay')
def test_forgot_password_request_nonexisting_user(mock_send_email, api_client):
    url = reverse('forgot_password_request')
    payload = {"email": "notfound@example.com"}
    
    response = api_client.post(url, payload)
    
    # Assert validation error returned
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data
    
    # Assert no OTP record was created
    assert PasswordResetOTP.objects.count() == 0
    
    # Assert no email task was triggered
    mock_send_email.assert_not_called()


@pytest.mark.django_db
def test_reset_password_success(api_client, test_user):
    # Setup OTP
    otp_record = PasswordResetOTP.objects.create(user=test_user, otp="123456")
    
    url = reverse('reset_password')
    payload = {
        "email": test_user.email,
        "otp": "123456",
        "password": "NewSecurePassword123!",
        "confirm_password": "NewSecurePassword123!"
    }
    
    response = api_client.post(url, payload)
    
    assert response.status_code == status.HTTP_200_OK
    assert "successfully reset" in response.data['message']
    
    # Check OTP marked as used
    otp_record.refresh_from_db()
    assert otp_record.is_used is True
    
    # Verify we can login with the new password
    login_url = reverse('token_obtain_pair')
    login_payload = {
        "username": test_user.username,
        "password": "NewSecurePassword123!"
    }
    login_response = api_client.post(login_url, login_payload)
    assert login_response.status_code == status.HTTP_200_OK
    assert "access" in login_response.data


@pytest.mark.django_db
def test_reset_password_invalid_otp(api_client, test_user):
    PasswordResetOTP.objects.create(user=test_user, otp="123456")
    
    url = reverse('reset_password')
    payload = {
        "email": test_user.email,
        "otp": "999999", # Incorrect OTP
        "password": "NewSecurePassword123!",
        "confirm_password": "NewSecurePassword123!"
    }
    
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "otp" in response.data


@pytest.mark.django_db
def test_reset_password_expired_otp(api_client, test_user):
    # Setup expired OTP (created 15 minutes ago)
    otp_record = PasswordResetOTP.objects.create(user=test_user, otp="123456")
    otp_record.created_at = timezone.now() - timezone.timedelta(minutes=15)
    otp_record.save(update_fields=['created_at'])
        
    url = reverse('reset_password')
    payload = {
        "email": test_user.email,
        "otp": "123456",
        "password": "NewSecurePassword123!",
        "confirm_password": "NewSecurePassword123!"
    }
    
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "otp" in response.data
    assert "expired" in str(response.data["otp"][0]).lower()


@pytest.mark.django_db
def test_reset_password_weak_password(api_client, test_user):
    PasswordResetOTP.objects.create(user=test_user, otp="123456")
    
    url = reverse('reset_password')
    payload = {
        "email": test_user.email,
        "otp": "123456",
        "password": "123", # Too short
        "confirm_password": "123"
    }
    
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password" in response.data
    
    # Test matching but common password
    payload["password"] = "password"
    payload["confirm_password"] = "password"
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password" in response.data


@pytest.mark.django_db
def test_verify_reset_otp_success(api_client, test_user):
    otp_record = PasswordResetOTP.objects.create(user=test_user, otp="123456")
    url = reverse('verify_reset_otp')
    payload = {
        "email": test_user.email,
        "otp": "123456"
    }
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_200_OK
    assert "verified successfully" in response.data['message']


@pytest.mark.django_db
def test_verify_reset_otp_invalid(api_client, test_user):
    PasswordResetOTP.objects.create(user=test_user, otp="123456")
    url = reverse('verify_reset_otp')
    payload = {
        "email": test_user.email,
        "otp": "999999"
    }
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "otp" in response.data


@pytest.mark.django_db
def test_login_using_email_success(api_client, test_user):
    # Set known password
    test_user.set_password("SecureUserPassword123!")
    test_user.save()

    url = reverse('token_obtain_pair')
    payload = {
        "username": test_user.email,
        "password": "SecureUserPassword123!"
    }
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "user" in response.data
    assert response.data["user"]["email"] == test_user.email


@pytest.mark.django_db
def test_login_using_username_success(api_client, test_user):
    # Set known password
    test_user.set_password("SecureUserPassword123!")
    test_user.save()

    url = reverse('token_obtain_pair')
    payload = {
        "username": test_user.username,
        "password": "SecureUserPassword123!"
    }
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "user" in response.data
    assert response.data["user"]["username"] == test_user.username


@pytest.mark.django_db
def test_login_using_email_or_username_invalid_password(api_client, test_user):
    test_user.set_password("SecureUserPassword123!")
    test_user.save()

    url = reverse('token_obtain_pair')
    
    # Check invalid password with email
    payload = {
        "username": test_user.email,
        "password": "WrongPassword123!"
    }
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Check invalid password with username
    payload["username"] = test_user.username
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
@patch('users.tasks.send_password_reset_email_task.delay')
def test_forgot_password_request_case_insensitive_and_invalidation(mock_send_email, api_client, test_user):
    # Setup an older OTP
    old_otp = PasswordResetOTP.objects.create(user=test_user, otp="111111")
    
    # Request with uppercase/mixedcase email
    mixed_case_email = test_user.email.upper()
    url = reverse('forgot_password_request')
    payload = {"email": mixed_case_email}
    
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_200_OK
    
    # Assert old OTP is marked as used (invalidated)
    old_otp.refresh_from_db()
    assert old_otp.is_used is True
    
    # Assert new OTP created
    new_otp = PasswordResetOTP.objects.filter(user=test_user, is_used=False).first()
    assert new_otp is not None
    assert new_otp.otp != "111111"



