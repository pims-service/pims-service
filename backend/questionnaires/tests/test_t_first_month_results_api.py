import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta
from users.models import User, Role
from questionnaires.models import Questionnaire, Question, ResponseSet

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
def first_month_user(db, participant_role):
    user = User.objects.create_user(
        username='first_month_user',
        email='first_month@test.com',
        password='password123',
        role=participant_role,
        has_completed_sociodemographic=True,
        onboarding_completed_at=timezone.now() - timedelta(days=30),
    )
    return user

@pytest.fixture
def posttest_questionnaire(db):
    q = Questionnaire.objects.create(
        title='Day 30 Follow-Up',
        is_posttest=True,
        is_active=True
    )
    Question.objects.create(questionnaire=q, content='First month Q1', type='TEXT', order=1)
    return q

@pytest.mark.django_db
class TestTFirstMonthResultsAPI:
    def test_admin_can_list_t_first_month_results(self, api_client, admin_user, posttest_questionnaire, first_month_user):
        # Create a completed T-First-Month response set (milestone='1_MONTH')
        rs = ResponseSet.objects.create(
            user=first_month_user,
            questionnaire=posttest_questionnaire,
            status='COMPLETED',
            milestone='1_MONTH',
            completed_at=timezone.now()
        )
        
        api_client.force_authenticate(user=admin_user)
        url = '/api/questionnaires/t-first-month-results/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == str(rs.id)

    def test_participant_cannot_list_t_first_month_results(self, api_client, first_month_user):
        api_client.force_authenticate(user=first_month_user)
        url = '/api/questionnaires/t-first-month-results/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_retrieve_t_first_month_detail(self, api_client, admin_user, posttest_questionnaire, first_month_user):
        rs = ResponseSet.objects.create(
            user=first_month_user,
            questionnaire=posttest_questionnaire,
            status='COMPLETED',
            milestone='1_MONTH',
            completed_at=timezone.now()
        )
        
        api_client.force_authenticate(user=admin_user)
        url = f'/api/questionnaires/t-first-month-results/{rs.id}/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(rs.id)
        assert response.data['questionnaire_title'] == 'Day 30 Follow-Up'
