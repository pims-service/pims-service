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
