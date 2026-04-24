import pytest
from rest_framework.test import APIClient
from users.models import User
from groups.models import Group
from phases.models import Phase
from django.core.cache import cache

@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_group(db):
    return Group.objects.create(name="Gratitude", description="Test Group")

@pytest.fixture
def test_user(db, test_group):
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="password123",
        group=test_group
    )
    return user

@pytest.fixture
def authenticated_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client

@pytest.fixture
def baseline_user(db, test_group):
    user = User.objects.create_user(
        username="baselineuser",
        email="baseline@example.com",
        password="password123",
        group=test_group,
        has_completed_baseline=True
    )
    return user

@pytest.fixture
def baseline_client(api_client, baseline_user):
    api_client.force_authenticate(user=baseline_user)
    return api_client

@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpassword"
    )

@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client

@pytest.fixture
def test_phase(db):
    from datetime import date, timedelta
    return Phase.objects.create(
        phase_number=1,
        name="Phase 1",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=7)
    )
