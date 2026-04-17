import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
def test_phase_list(baseline_client, test_phase):
    url = reverse('phase_list')
    response = baseline_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) >= 1

@pytest.mark.django_db
def test_current_phase(baseline_client, test_phase):
    url = reverse('current_phase')
    response = baseline_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['name'] == "Phase 1"
