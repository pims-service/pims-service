import pytest
from users.models import User


@pytest.mark.django_db
def test_has_completed_baseline_default_is_false(test_user):
    assert test_user.has_completed_baseline is False


@pytest.mark.django_db
def test_has_completed_baseline_updates_to_true(test_user):
    test_user.has_completed_baseline = True
    test_user.save(update_fields=['has_completed_baseline'])

    test_user.refresh_from_db()
    assert test_user.has_completed_baseline is True


@pytest.mark.django_db
def test_new_user_starts_with_false(db):
    user = User.objects.create_user(
        username="freshuser",
        email="fresh@example.com",
        password="password123"
    )
    assert user.has_completed_baseline is False

@pytest.mark.django_db
def test_completion_rate_caching(test_user):
    from django.utils import timezone
    from django.core.cache import cache
    from activities.models import Activity, Submission
    from phases.models import Phase

    # Setup user in experiment
    test_user.has_completed_baseline = True
    test_user.baseline_completed_at = timezone.now() - timezone.timedelta(days=2) # Day 3
    test_user.save()

    phase = Phase.objects.create(
        phase_number=1, 
        name="Phase 1", 
        start_date=timezone.now().date() - timezone.timedelta(days=10),
        end_date=timezone.now().date() + timezone.timedelta(days=10)
    )
    activity = Activity.objects.create(title="A1", assigned_phase=phase, day_number=1)
    
    # Ensure cache is clean
    cache_key = f"user_{test_user.user_id}_completion_rate"
    cache.delete(cache_key)

    # First call - calculates and caches
    rate1 = test_user.completion_rate
    assert cache.get(cache_key) == rate1

    # Add a submission manually behind the scenes
    Submission.objects.create(user=test_user, activity=activity, experiment_day=1)
    
    # Second call - should still return cached (old) value if not for the signal
    # But wait, our signal clears it! So rate2 should be different.
    rate2 = test_user.completion_rate
    assert rate2 > rate1
    assert cache.get(cache_key) == rate2

@pytest.mark.django_db
def test_current_experiment_day_caching(test_user):
    from django.utils import timezone
    from django.core.cache import cache

    test_user.has_completed_baseline = True
    test_user.baseline_completed_at = timezone.now() - timezone.timedelta(days=1) # Day 2
    test_user.save()

    cache_key = f"user_{test_user.user_id}_exp_day"
    cache.delete(cache_key)

    day = test_user.current_experiment_day
    assert day == 2
    assert cache.get(cache_key) == 2
