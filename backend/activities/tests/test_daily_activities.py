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
            group=group, has_completed_sociodemographic=True,
            onboarding_completed_at=timezone.now()
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
            group=group, has_completed_sociodemographic=True,
            onboarding_completed_at=timezone.now()
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
        words_20 = "word " * 20
        payload = {
            "activity": activity.id,
            "entry_1": words_20,
            "entry_2": words_20,
            "entry_3": words_20
        }
        
        # 1. First submission (10:00 AM)
        resp1 = api_client.post(submit_url, payload, format='json')
        assert resp1.status_code == status.HTTP_201_CREATED
        
        # 2. Re-submit same day (11:59 PM PKT, which is 18:59:59 UTC) - Should be blocked (Locked)
        with freeze_time("2026-04-19 18:59:59"):
            from django.core.cache import cache
            cache.clear()
            resp2 = api_client.post(submit_url, {
                "activity": activity.id,
                "entry_1": words_20 + " extra",
                "entry_2": words_20 + " extra",
                "entry_3": words_20 + " extra"
            }, format='json')
            assert resp2.status_code == status.HTTP_400_BAD_REQUEST
            assert "already been submitted and is locked" in resp2.data['detail']
            
        # 3. Submit next day (e.g. 10:00 AM the next day, which is a new UTC day)
        with freeze_time("2026-04-20 10:00:00"):
            cache.clear()
            # Create a Day 2 activity to satisfy the new validation
            # (User is now on Day 2 because baseline was at 10:00 AM on 2026-04-19)
            activity_day2 = Activity.objects.create(
                title="Gratitude Reflection Day 2",
                description="Day 2 prompt",
                assigned_phase=activity.assigned_phase,
                group=group,
                activity_type="paragraph",
                day_number=2
            )
            resp3 = api_client.post(submit_url, {
                "activity": activity_day2.id,
                "entry_1": words_20,
                "entry_2": words_20,
                "entry_3": words_20
            }, format='json')
            assert resp3.status_code == status.HTTP_201_CREATED, resp3.data

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
        words_20 = "word " * 20
        payload = {
            "activity": other_activity.id,
            "entry_1": words_20,
            "entry_2": words_20,
            "entry_3": words_20
        }
        
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
    def test_block_duplicate_daily_submission(self, api_client, test_phase):
        """
        Verify that submitting again on the same day is blocked because the entries are locked.
        """
        user, group, activity = self.create_context(test_phase)
        user.onboarding_completed_at = datetime(2026, 5, 1, 0, 0, tzinfo=dt_timezone.utc)
        user.save()
        
        api_client.force_authenticate(user=user)
        
        url = reverse('daily-activity-submit')
        words_20 = "word " * 20
        payload = {
            "activity": activity.id,
            "entry_1": words_20,
            "entry_2": words_20,
            "entry_3": words_20
        }
        api_client.post(url, payload, format='json')
        
        # Second submission should be blocked
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already been submitted and is locked" in response.data['detail']
        assert Submission.objects.filter(user=user).count() == 1
