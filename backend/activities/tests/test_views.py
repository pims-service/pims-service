import pytest
from django.urls import reverse
from rest_framework import status
from activities.models import Activity

@pytest.mark.django_db
def test_activity_list_current_phase(baseline_client, test_phase):
    Activity.objects.create(
        title="Test Activity",
        description="Desc",
        assigned_phase=test_phase,
        activity_type="paragraph"
    )
    url = reverse('activity_list')
    response = baseline_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1

@pytest.mark.django_db
def test_submission_create(baseline_client, test_phase):
    activity = Activity.objects.create(
        title="Test Submission",
        description="Desc",
        assigned_phase=test_phase,
        activity_type="paragraph"
    )
    url = reverse('submission_create')
    data = {
        "activity": activity.id,
        "content": "My daily entry."
    }
    response = baseline_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
