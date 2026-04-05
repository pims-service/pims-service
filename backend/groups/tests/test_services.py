import pytest

from groups.models import Group
from groups.services import assign_group
from users.models import User


@pytest.mark.django_db
def test_assign_group_raises_when_no_groups():
    with pytest.raises(Group.DoesNotExist):
        assign_group()


@pytest.mark.django_db
def test_assign_group_returns_only_group():
    group = Group.objects.create(name="Solo", description="")
    assert assign_group() == group


@pytest.mark.django_db
def test_assign_group_returns_least_filled():
    g1 = Group.objects.create(name="Group A", description="")
    g2 = Group.objects.create(name="Group B", description="")
    User.objects.create_user(username="u1", email="u1@example.com", password="pass1234", group=g1)
    # g2 has 0 participants; g1 has 1 – service must return g2
    assert assign_group() == g2


@pytest.mark.django_db
def test_assign_group_breaks_ties_by_pk():
    g1 = Group.objects.create(name="Group A", description="")
    g2 = Group.objects.create(name="Group B", description="")
    # Both empty – lower pk wins
    assert assign_group() == g1


@pytest.mark.django_db
def test_assign_group_balances_distribution():
    groups = [Group.objects.create(name=f"Group {i}", description="") for i in range(4)]
    for i in range(8):
        group = assign_group()
        User.objects.create_user(
            username=f"user{i}",
            email=f"u{i}@example.com",
            password="pass1234",
            group=group,
        )
    for g in groups:
        assert g.participants.count() == 2
