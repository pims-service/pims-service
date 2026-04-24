import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from django.core.cache import cache
from freezegun import freeze_time
from datetime import timedelta
from activities.models import Activity, Submission
from groups.models import Group
from users.models import User
from activities.tasks import sync_user_experiment_state

@pytest.fixture
def timeline_setup(db, test_phase):
    with freeze_time("2026-04-24 10:00:00"):
        group = Group.objects.create(name="Timeline Group")
        user = User.objects.create_user(
            username="timeline_user", email="tl@test.com", password="pwd",
            group=group, has_completed_baseline=True,
            baseline_completed_at=timezone.now()
        )
        # Create activities for Day 1 and Day 2
        act1 = Activity.objects.create(
            title="Day 1 Task", description="Task 1",
            assigned_phase=test_phase, group=group,
            activity_type="task", day_number=1
        )
        act2 = Activity.objects.create(
            title="Day 2 Task", description="Task 2",
            assigned_phase=test_phase, group=group,
            activity_type="task", day_number=2
        )
        return user, group, act1, act2

@freeze_time("2026-04-24 10:00:00")
@pytest.mark.django_db
class TestTimelineAndCaching:
    
    def test_serving_activity_based_on_relative_day(self, api_client, timeline_setup):
        """Verify that the user sees Day 1 activity immediately after baseline."""
        user, group, act1, act2 = timeline_setup
        api_client.force_authenticate(user=user)
        
        url = reverse('daily-activity-current')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == act1.id
        assert response.data['current_day'] == 1

    def test_day_transition_at_midnight(self, api_client, timeline_setup):
        """Verify that the activity switches to Day 2 after midnight."""
        user, group, act1, act2 = timeline_setup
        api_client.force_authenticate(user=user)
        
        # Initial is Day 1
        assert user.current_experiment_day == 1
        
        # Travel to tomorrow
        tomorrow = timezone.now() + timedelta(days=1)
        with freeze_time(tomorrow):
            # Clear cache for the test to ensure fresh calculation or verify cache behavior
            cache.delete(f"user_{user.user_id}_exp_day")
            
            response = api_client.get(reverse('daily-activity-current'))
            assert response.status_code == status.HTTP_200_OK
            assert response.data['id'] == act2.id
            assert response.data['current_day'] == 2

    def test_redis_caching_of_experiment_day(self, timeline_setup):
        """Verify that the experimental day is cached in Redis."""
        user, group, act1, act2 = timeline_setup
        
        # First call calculates and caches
        day = user.current_experiment_day
        assert day == 1
        
        cache_key = f"user_{user.user_id}_exp_day"
        assert cache.get(cache_key) == 1
        
        # Manually change the date in DB but keep cache - should still return 1
        user.baseline_completed_at = user.baseline_completed_at - timedelta(days=5)
        user.save()
        
        assert user.current_experiment_day == 1 # Hits cache

    def test_submission_persists_experiment_day(self, api_client, timeline_setup):
        """Verify that submissions store the chronological day of the experiment."""
        user, group, act1, act2 = timeline_setup
        api_client.force_authenticate(user=user)
        
        # Travel to Day 3
        three_days_ago = timezone.now() - timedelta(days=2)
        user.baseline_completed_at = three_days_ago
        user.save()
        cache.clear() # Ensure clean state

        url = reverse('daily-activity-submit')
        payload = {"activity": act1.id, "content": "Day 3 entry"} # User can submit any activity for their group
        
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        submission = Submission.objects.get(user=user, content="Day 3 entry")
        assert submission.experiment_day == 3

    def test_redis_submission_flag_caching(self, api_client, timeline_setup):
        """Verify that submitted_today flag is cached in Redis after submission."""
        user, group, act1, act2 = timeline_setup
        api_client.force_authenticate(user=user)
        
        cache_key = f"user_{user.user_id}_submitted_{timezone.now().date()}"
        assert cache.get(cache_key) is None
        
        # Submit
        api_client.post(reverse('daily-activity-submit'), {"activity": act1.id, "content": "..."})
        
        # Should now be in cache
        assert cache.get(cache_key) is True
        
        # Current endpoint should reflect this immediately from cache
        response = api_client.get(reverse('daily-activity-current'))
        assert response.data['submitted_today'] is True

    def test_sync_task_repopulates_cache(self, timeline_setup):
        """Verify the Celery task correctly re-syncs the Redis state."""
        user, group, act1, act2 = timeline_setup
        cache.clear()
        
        # Mock a submission without updating cache
        Submission.objects.create(user=user, activity=act1, content="...", experiment_day=1)
        
        assert cache.get(f"user_{user.user_id}_submitted_{timezone.now().date()}") is None
        
        # Run task
        sync_user_experiment_state(user.user_id)
        
        # Cache should be populated
        assert cache.get(f"user_{user.user_id}_submitted_{timezone.now().date()}") is True
        assert cache.get(f"user_{user.user_id}_exp_day") == 1
