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
def day8_user(db, participant_role):
    user = User.objects.create_user(
        username='day8_user',
        email='day8@test.com',
        password='password123',
        role=participant_role,
        has_completed_sociodemographic=True,
        onboarding_completed_at=timezone.now() - timedelta(days=7),
    )
    return user

@pytest.fixture
def early_user(db, participant_role):
    user = User.objects.create_user(
        username='early_user',
        email='early@test.com',
        password='password123',
        role=participant_role,
        has_completed_sociodemographic=True,
        onboarding_completed_at=timezone.now() - timedelta(days=3),
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
class TestT1ResultsAPI:
    def test_admin_can_list_t1_results(self, api_client, admin_user, posttest_questionnaire, day8_user):
        # Create a completed T1 response set (milestone='7_DAYS')
        rs = ResponseSet.objects.create(
            user=day8_user,
            questionnaire=posttest_questionnaire,
            status='COMPLETED',
            milestone='7_DAYS',
            completed_at=timezone.now()
        )
        
        api_client.force_authenticate(user=admin_user)
        url = '/api/questionnaires/t1-results/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == str(rs.id)

    def test_participant_cannot_list_t1_results(self, api_client, day8_user):
        api_client.force_authenticate(user=day8_user)
        url = '/api/questionnaires/t1-results/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_retrieve_t1_detail(self, api_client, admin_user, posttest_questionnaire, day8_user):
        rs = ResponseSet.objects.create(
            user=day8_user,
            questionnaire=posttest_questionnaire,
            status='COMPLETED',
            milestone='7_DAYS',
            completed_at=timezone.now()
        )
        
        api_client.force_authenticate(user=admin_user)
        url = f'/api/questionnaires/t1-results/{rs.id}/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(rs.id)
        assert response.data['questionnaire_title'] == 'Day 7 Post-Test'
