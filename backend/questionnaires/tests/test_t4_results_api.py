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
def year1_user(db, participant_role):
    user = User.objects.create_user(
        username='year1_user',
        email='year1@test.com',
        password='password123',
        role=participant_role,
        has_completed_sociodemographic=True,
        onboarding_completed_at=timezone.now() - timedelta(days=400),
        has_completed_posttest=True,
        posttest_completed_at=timezone.now() - timedelta(days=370),
    )
    return user

@pytest.fixture
def posttest_questionnaire(db):
    q = Questionnaire.objects.create(
        title='Longitudinal Psychometric Scales',
        is_posttest=True,
        is_active=True,
        assessment_type='PSYCHOMETRIC',
    )
    Question.objects.create(questionnaire=q, content='[PERMA] T4 Q1', type='TEXT', order=1)
    return q

@pytest.mark.django_db
class TestT4ResultsAPI:
    def test_admin_can_list_t4_results(self, api_client, admin_user, posttest_questionnaire, year1_user):
        rs = ResponseSet.objects.create(
            user=year1_user,
            questionnaire=posttest_questionnaire,
            status='COMPLETED',
            milestone='1_YEAR',
            completed_at=timezone.now()
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/questionnaires/t4-results/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == str(rs.id)

    def test_participant_cannot_list_t4_results(self, api_client, year1_user):
        api_client.force_authenticate(user=year1_user)
        response = api_client.get('/api/questionnaires/t4-results/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_retrieve_t4_detail(self, api_client, admin_user, posttest_questionnaire, year1_user):
        rs = ResponseSet.objects.create(
            user=year1_user,
            questionnaire=posttest_questionnaire,
            status='COMPLETED',
            milestone='1_YEAR',
            completed_at=timezone.now()
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/questionnaires/t4-results/{rs.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(rs.id)
        assert response.data['questionnaire_title'] == 'Longitudinal Psychometric Scales'
