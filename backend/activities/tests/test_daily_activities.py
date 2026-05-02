import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from freezegun import freeze_time
from datetime import datetime, timedelta, timezone as dt_timezone
import uuid

from activities.models import Activity, Submission
from groups.models import Group
from users.models import User

@pytest.fixture
def test_setup(db, test_phase):
    """
    Ensures user and activity are in the SAME group for reliable testing.
    """
    with freeze_time("2026-04-19 10:00:00"):
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
    Includes verification for logging, integrity, and timeline logic.
    """

    def create_context(self, test_phase):
        uid = uuid.uuid4().hex[:8]
        group = Group.objects.create(name=f"Group_{uid}")
        user = User.objects.create_user(
            username=f"user_{uid}", email=f"user_{uid}@test.com", password="pwd",
            group=group, has_completed_baseline=True,
            baseline_completed_at=timezone.now()
        )
        activity = Activity.objects.create(
            title=f"Activity_{uid}", group=group, activity_type="paragraph",
            assigned_phase=test_phase, day_number=1
        )
        return user, group, activity

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
        
        # 2. Re-submit same day (11:59 PM) - Should succeed (Update)
        with freeze_time("2026-04-19 23:59:59"):
            resp2 = api_client.post(submit_url, {"activity": activity.id, "content": "Updated Entry"}, format='json')
            assert resp2.status_code == status.HTTP_201_CREATED
            assert Submission.objects.get(id=resp1.data['id']).content == "Updated Entry"
            
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
            assigned_phase=activity.assigned_phase,
            day_number=1
        )
        
        url = reverse('daily-activity-submit')
        payload = {"activity": other_activity.id, "content": "Sneaky"}
        
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not assigned to your group" in response.data['non_field_errors'][0]

    def test_request_id_in_response(self, api_client, test_phase):
        user, _, _ = self.create_context(test_phase)
        api_client.force_authenticate(user=user)
        response = api_client.get(reverse('daily-activity-current'))
        assert response.status_code == status.HTTP_200_OK
        assert 'X-Request-ID' in response

    @freeze_time("2026-05-01 10:00:00")
    def test_update_daily_submission(self, api_client, test_phase):
        """
        Verify that submitting again on the same day updates the existing record.
        """
        user, group, activity = self.create_context(test_phase)
        user.baseline_completed_at = datetime(2026, 5, 1, 0, 0, tzinfo=dt_timezone.utc)
        user.save()
        
        api_client.force_authenticate(user=user)
        
        url = reverse('daily-activity-submit')
        api_client.post(url, {"activity": activity.id, "content": "Initial"}, format='json')
        
        # Update
        response = api_client.post(url, {"activity": activity.id, "content": "Revised"}, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Submission.objects.filter(user=user).count() == 1
        assert Submission.objects.get(user=user).content == "Revised"
