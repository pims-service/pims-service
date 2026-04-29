import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta
from users.models import User, Role
from questionnaires.models import Questionnaire, Question, Option, ResponseSet

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user(db):
    user = User.objects.create_superuser(
        username='admin',
        email='admin@test.com',
        password='adminpassword'
    )
    return user

@pytest.fixture
def participant_role(db):
    return Role.objects.get_or_create(name='Participant')[0]

@pytest.fixture
def day7_user(db, participant_role):
    user = User.objects.create_user(
        username='day7_user',
        email='day7@test.com',
        password='password123',
        role=participant_role,
        has_completed_baseline=True,
        baseline_completed_at=timezone.now() - timedelta(days=7)
    )
    return user

@pytest.fixture
def early_user(db, participant_role):
    user = User.objects.create_user(
        username='early_user',
        email='early@test.com',
        password='password123',
        role=participant_role,
        has_completed_baseline=True,
        baseline_completed_at=timezone.now() - timedelta(days=3)
    )
    return user

@pytest.fixture
def posttest_questionnaire(db):
    q = Questionnaire.objects.create(
        title='Day 7 Post-Test',
        is_posttest=True,
        is_active=True
    )
    Question.objects.create(questionnaire=q, content='Post-test Q1', type='TEXT', order=1)
    return q

@pytest.mark.django_db
class TestPosttestAPI:
    def test_admin_can_list_posttests(self, api_client, admin_user, posttest_questionnaire, day7_user):
        # Create a completed post-test
        rs = ResponseSet.objects.create(
            user=day7_user,
            questionnaire=posttest_questionnaire,
            status='COMPLETED',
            completed_at=timezone.now()
        )
        
        api_client.force_authenticate(user=admin_user)
        url = '/api/questionnaires/posttests/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # The response is paginated
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == str(rs.id)

    def test_participant_cannot_list_posttests(self, api_client, day7_user):
        api_client.force_authenticate(user=day7_user)
        url = '/api/questionnaires/posttests/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_participant_can_create_posttest_when_due(self, api_client, day7_user, posttest_questionnaire):
        api_client.force_authenticate(user=day7_user)
        url = '/api/questionnaires/response-sets/'
        response = api_client.post(url, {'questionnaire': str(posttest_questionnaire.id)})
        
        assert response.status_code == status.HTTP_201_CREATED
        assert str(response.data['questionnaire']) == str(posttest_questionnaire.id)

    def test_participant_cannot_create_posttest_early(self, api_client, early_user, posttest_questionnaire):
        api_client.force_authenticate(user=early_user)
        url = '/api/questionnaires/response-sets/'
        response = api_client.post(url, {'questionnaire': str(posttest_questionnaire.id)})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Post-test is not available yet" in str(response.data['detail'])

    def test_global_analytics_endpoint(self, api_client, admin_user, posttest_questionnaire, day7_user):
        # Create 2 completions
        ResponseSet.objects.create(user=day7_user, questionnaire=posttest_questionnaire, status='COMPLETED')
        
        api_client.force_authenticate(user=admin_user)
        url = '/api/questionnaires/analytics/all/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Find the posttest in the list
        posttest_stat = next(item for item in response.data if item['questionnaire_id'] == str(posttest_questionnaire.id))
        assert posttest_stat['total_completions'] == 1
        assert posttest_stat['title'] == 'Day 7 Post-Test'
