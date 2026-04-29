import pytest
from django.urls import reverse
from rest_framework import status


# ---------------------------------------------------------------------------
# GET /api/groups/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_group_list_authenticated(authenticated_client, test_group):
    url = reverse('group_list')
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) >= 1


@pytest.mark.django_db
def test_group_list_unauthenticated(api_client):
    url = reverse('group_list')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_group_list_contains_member_count(authenticated_client, test_group):
    """member_count field must be present; authenticated_client includes test_user
    who belongs to test_group, so count is >= 0."""
    url = reverse('group_list')
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    group_data = next(g for g in response.data if g['group_id'] == test_group.group_id)
    assert 'member_count' in group_data
    assert isinstance(group_data['member_count'], int)


@pytest.mark.django_db
def test_group_list_member_count_reflects_participants(authenticated_client, test_group, test_user):
    """member_count must equal the number of users assigned to the group."""
    url = reverse('group_list')
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    group_data = next(g for g in response.data if g['group_id'] == test_group.group_id)
    assert group_data['member_count'] == 1  # test_user is in test_group


# ---------------------------------------------------------------------------
# GET /api/groups/<id>/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_group_detail_authenticated(authenticated_client, test_group):
    url = reverse('group-detail', kwargs={'pk': test_group.group_id})
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['group_id'] == test_group.group_id
    assert response.data['name'] == test_group.name


@pytest.mark.django_db
def test_group_detail_unauthenticated(api_client, test_group):
    url = reverse('group-detail', kwargs={'pk': test_group.group_id})
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_group_detail_contains_participants(authenticated_client, test_group, test_user):
    url = reverse('group-detail', kwargs={'pk': test_group.group_id})
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert 'participants' in response.data
    assert len(response.data['participants']) == 1
    participant = response.data['participants'][0]
    assert participant['user_id'] == test_user.user_id
    assert participant['full_name'] == test_user.full_name
    assert 'current_experiment_day' in participant


@pytest.mark.django_db
def test_group_detail_contains_member_count(authenticated_client, test_group, test_user):
    url = reverse('group-detail', kwargs={'pk': test_group.group_id})
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['member_count'] == 1


@pytest.mark.django_db
def test_group_detail_not_found(authenticated_client):
    url = reverse('group-detail', kwargs={'pk': 99999})
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# PATCH /api/groups/<id>/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_group_patch_by_admin(admin_client, test_group):
    url = reverse('group-detail', kwargs={'pk': test_group.group_id})
    response = admin_client.patch(url, {'name': 'Updated Name'}, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['name'] == 'Updated Name'


@pytest.mark.django_db
def test_group_patch_description_by_admin(admin_client, test_group):
    url = reverse('group-detail', kwargs={'pk': test_group.group_id})
    response = admin_client.patch(url, {'description': 'New description'}, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['description'] == 'New description'


@pytest.mark.django_db
def test_group_patch_forbidden_for_non_admin(authenticated_client, test_group):
    url = reverse('group-detail', kwargs={'pk': test_group.group_id})
    response = authenticated_client.patch(url, {'name': 'Hacked'}, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_group_patch_forbidden_unauthenticated(api_client, test_group):
    url = reverse('group-detail', kwargs={'pk': test_group.group_id})
    response = api_client.patch(url, {'name': 'Hacked'}, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# DELETE /api/groups/<id>/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_group_delete_by_admin(admin_client, test_group):
    url = reverse('group-detail', kwargs={'pk': test_group.group_id})
    response = admin_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_group_delete_forbidden_for_non_admin(authenticated_client, test_group):
    url = reverse('group-detail', kwargs={'pk': test_group.group_id})
    response = authenticated_client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_group_delete_forbidden_unauthenticated(api_client, test_group):
    url = reverse('group-detail', kwargs={'pk': test_group.group_id})
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
