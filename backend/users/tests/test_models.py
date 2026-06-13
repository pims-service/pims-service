import pytest
from users.models import User


@pytest.mark.django_db
def test_has_completed_sociodemographic_default_is_false(test_user):
    assert test_user.has_completed_sociodemographic is False


@pytest.mark.django_db
def test_has_completed_sociodemographic_updates_to_true(test_user):
    test_user.has_completed_sociodemographic = True
    test_user.save(update_fields=['has_completed_sociodemographic'])

    test_user.refresh_from_db()
    assert test_user.has_completed_sociodemographic is True


@pytest.mark.django_db
def test_new_user_starts_with_false(db):
    user = User.objects.create_user(
        username="freshuser",
        email="fresh@example.com",
        password="password123"
    )
    assert user.has_completed_sociodemographic is False

@pytest.mark.django_db
def test_current_experiment_day_caching(test_user):
    from django.utils import timezone
    from django.core.cache import cache

    test_user.has_completed_sociodemographic = True
    test_user.onboarding_completed_at = timezone.now() - timezone.timedelta(days=1) # Day 2
    test_user.save()

    cache_key = f"user_{test_user.user_id}_activity_state"
    cache.delete(cache_key)

    day = test_user.current_experiment_day
    assert day == 2
    assert cache.get(cache_key).day_in_block == 2


@pytest.mark.django_db
def test_is_t2_due(test_user):
    from django.utils import timezone
    from datetime import timedelta

    test_user.has_completed_sociodemographic = True
    
    # 1. When onboarding completed at is not set, is_t2_due should be False
    test_user.onboarding_completed_at = None
    test_user.has_completed_t2 = False
    test_user.save()
    assert test_user.is_t2_due is False

    # 2. When onboarding completed at is set, but < 90 days ago, is_t2_due should be False
    test_user.onboarding_completed_at = timezone.now() - timedelta(days=89)
    test_user.save()
    assert test_user.is_t2_due is False

    # 3. When onboarding completed at is set and >= 90 days ago, is_t2_due should be True
    test_user.onboarding_completed_at = timezone.now() - timedelta(days=90)
    test_user.save()
    assert test_user.is_t2_due is True

    # 4. When already completed, is_t2_due should be False
    test_user.has_completed_t2 = True
    test_user.save()
    assert test_user.is_t2_due is False

