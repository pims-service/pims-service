import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
def test_user_profile(authenticated_client, test_user):
    url = reverse('profile')
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['username'] == test_user.username

@pytest.mark.django_db
def test_admin_user_list(admin_client, test_user):
    url = reverse('admin_user_list')
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) >= 1
