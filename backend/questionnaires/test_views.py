import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User
from questionnaires.models import Questionnaire, ResponseSet

@pytest.fixture
def user_a(db):
    return User.objects.create_user(username='usera', email='usera@example.com', password='pw')

@pytest.fixture
def user_b(db):
    return User.objects.create_user(username='userb', email='userb@example.com', password='pw')

@pytest.fixture
def test_questionnaire(db):
    return Questionnaire.objects.create(title='Test')

@pytest.mark.django_db
class TestResponseSetIsolation:
    def test_user_can_only_see_own_responses(self, api_client, user_a, user_b, test_questionnaire):
        """Ensure the backend API filters querysets exclusively for the authenticated user."""
        
        # Cross-pollinate the database
        rs_a = ResponseSet.objects.create(user=user_a, questionnaire=test_questionnaire)
        rs_b = ResponseSet.objects.create(user=user_b, questionnaire=test_questionnaire)

        api_client.force_authenticate(user=user_a)
        response = api_client.get(reverse('response_set_list_create'))
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Responses should be a direct list (no pagination in global settings)
        assert isinstance(data, list)
        assert len(data) == 1
        # The returned response set MUST belong to User A
        assert data[0]['id'] == str(rs_a.id)

        # Authenticate as opposite user
        api_client.force_authenticate(user=user_b)
        response = api_client.get(reverse('response_set_list_create'))
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # User B should only see 1 response set and it must be theirs
        assert len(data) == 1
        assert data[0]['id'] == str(rs_b.id)

    def test_admin_baseline_list_pagination(self, admin_client, user_a, test_questionnaire):
        """Verify the admin baselines endpoint returns paginated results."""
        test_questionnaire.is_baseline = True
        test_questionnaire.save()
        
        # Create a completed response set
        ResponseSet.objects.create(user=user_a, questionnaire=test_questionnaire, status='COMPLETED')
        
        admin_client.force_authenticate(user=User.objects.create_superuser(username='admin2', email='a2@b.com', password='pw'))
        response = admin_client.get(reverse('admin_baseline_list'))
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'results' in data
        assert 'count' in data
        assert isinstance(data['results'], list)
        assert data['count'] >= 1
