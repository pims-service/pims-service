import pytest
from groups.models import Group

@pytest.mark.django_db
def test_group_creation():
    group = Group.objects.create(name="Relationships", description="Test Description")
    assert group.name == "Relationships"
    assert str(group) == "Relationships"
