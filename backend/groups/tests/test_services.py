import pytest

from groups.models import Group
from groups.services import assign_group
from users.models import User


@pytest.mark.django_db
def test_assign_group_raises_when_no_groups():
    Group.objects.all().delete()
    with pytest.raises(Group.DoesNotExist):
        assign_group()


@pytest.mark.django_db
def test_assign_group_returns_only_group():
    Group.objects.all().delete()
    group = Group.objects.create(name="Svc_Solo", description="", is_active=True, capacity=50)
    assert assign_group() == group


@pytest.mark.django_db
def test_assign_group_returns_least_filled():
    Group.objects.all().delete()
    g1 = Group.objects.create(name="Svc_Group_A", description="", is_active=True, capacity=50)
    g2 = Group.objects.create(name="Svc_Group_B", description="", is_active=True, capacity=50)
    User.objects.create_user(username="test_u1", email="test_u1@example.com", password="pass1234", group=g1)
    # g2 has 0 participants; g1 has 1 – service must return g2
    assert assign_group() == g2


@pytest.mark.django_db
def test_assign_group_breaks_ties_by_pk():
    Group.objects.all().delete()
    g1 = Group.objects.create(name="Svc_Group_Tie_A", description="", is_active=True, capacity=50)
    g2 = Group.objects.create(name="Svc_Group_Tie_B", description="", is_active=True, capacity=50)
    # Both empty – lower pk wins
    assert assign_group() == g1


@pytest.mark.django_db
def test_assign_group_balances_distribution():
    # Clear any leftover groups from other tests/fixtures to ensure pure distribution
    Group.objects.all().delete()
    groups = [Group.objects.create(name=f"Svc_Group_Dist_{i}", description="", is_active=True, capacity=50) for i in range(4)]
    for i in range(8):
        group = assign_group()
        User.objects.create_user(
            username=f"test_dist_user{i}",
            email=f"test_u{i}@example.com",
            password="pass1234",
            group=group,
        )
    for g in groups:
        assert g.participants.count() == 2


@pytest.mark.django_db
def test_assign_group_skips_inactive():
    Group.objects.all().delete()
    g_inactive = Group.objects.create(name="Inactive", description="", is_active=False, capacity=50)
    g_active = Group.objects.create(name="Active", description="", is_active=True, capacity=50)
    assert assign_group() == g_active


@pytest.mark.django_db
def test_assign_group_skips_full_capacity():
    Group.objects.all().delete()
    g_full = Group.objects.create(name="Full", description="", is_active=True, capacity=1)
    g_available = Group.objects.create(name="Available", description="", is_active=True, capacity=50)
    User.objects.create_user(username="cap_user", email="cap@example.com", password="pass1234", group=g_full)
    # g_full is at capacity (1/1), so g_available should be returned
    assert assign_group() == g_available
