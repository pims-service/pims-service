import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
def test_group_list_authenticated(authenticated_client, test_group):
    url = reverse('group_list')
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) >= 1

@pytest.mark.django_db
def test_group_list_unauthenticated(api_client):
    url = reverse('group_list')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
