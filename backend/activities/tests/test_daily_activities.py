import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from freezegun import freeze_time
from datetime import datetime, timedelta

from activities.models import Activity, Submission
from groups.models import Group
from users.models import User

@freeze_time("2026-04-19 10:00:00")
@pytest.fixture
def test_setup(db, test_phase):
    """
    Ensures user and activity are in the SAME group for reliable testing.
    """
    group = Group.objects.create(name="Gratitude", description="Test")
    user = User.objects.create_user(
        username="daily_user", email="daily@test.com", password="pwd",
        group=group, has_completed_baseline=True,
        baseline_completed_at=timezone.now()
    )
    activity = Activity.objects.create(
        title="Gratitude Reflection",
        description="Write 3 things...",
        assigned_phase=test_phase,
        group=group,
        activity_type="paragraph",
        day_number=1
    )
    return user, group, activity

@freeze_time("2026-04-19 10:00:00")
@pytest.mark.django_db
class TestDailyActivities:
    """
    Production-grade tests for the Daily Activity system.
    Self-contained fixtures ensure zero cross-test contamination.
    """

    def test_get_current_activity_serves_correct_group_prompt(self, api_client, test_setup):
        """Verify that a user only sees the activity assigned to their group."""
        user, group, activity = test_setup
        api_client.force_authenticate(user=user)
        
        url = reverse('daily-activity-current')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == activity.id
        assert response.data['submitted_today'] is False

    def test_midnight_reset_logic(self, api_client, test_setup):
        user, group, activity = test_setup
        api_client.force_authenticate(user=user)
        
        submit_url = reverse('daily-activity-submit')
        payload = {"activity": activity.id, "content": "Entry 1"}
        
        # 1. First submission (10:00 AM)
        resp1 = api_client.post(submit_url, payload, format='json')
        assert resp1.status_code == status.HTTP_201_CREATED
        
        # 2. Re-submit same day (11:59 PM)
        with freeze_time("2026-04-19 23:59:59"):
            resp2 = api_client.post(submit_url, payload, format='json')
            assert resp2.status_code == status.HTTP_400_BAD_REQUEST
            
        # 3. Submit next day (00:01 AM)
        with freeze_time("2026-04-20 00:00:01"):
            resp3 = api_client.post(submit_url, {"activity": activity.id, "content": "Entry 2"}, format='json')
            assert resp3.status_code == status.HTTP_201_CREATED

    def test_prevent_submission_for_wrong_group(self, api_client, test_setup):
        user, group, activity = test_setup
        api_client.force_authenticate(user=user)
        
        other_group = Group.objects.create(name="Other")
        other_activity = Activity.objects.create(
            title="Other", group=other_group, activity_type="paragraph",
            assigned_phase=activity.assigned_phase
        )
        
        url = reverse('daily-activity-submit')
        payload = {"activity": other_activity.id, "content": "Sneaky"}
        
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not assigned to your group" in response.data['non_field_errors'][0]
