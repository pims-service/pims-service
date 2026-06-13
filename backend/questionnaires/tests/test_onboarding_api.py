import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from users.models import User, Role
from questionnaires.models import Questionnaire, Question, Option, ResponseSet

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def participant_role(db):
    return Role.objects.get_or_create(name='Participant')[0]

@pytest.fixture
def fresh_user(db, participant_role):
    return User.objects.create_user(
        username='fresh_user',
        email='fresh@test.com',
        password='password123',
        role=participant_role,
        has_completed_sociodemographic=False
    )

@pytest.fixture
def onboarded_user(db, participant_role):
    return User.objects.create_user(
        username='onboarded_user',
        email='onboarded@test.com',
        password='password123',
        role=participant_role,
        has_completed_sociodemographic=True,
        onboarding_completed_at=timezone.now()
    )

@pytest.fixture
def socio_questionnaire(db):
    q = Questionnaire.objects.create(
        title='Sociodemographic Questionnaire',
        assessment_type='SOCIODEMOGRAPHIC',
        is_active=True
    )
    Question.objects.create(questionnaire=q, content='Age?', type='CHOICE', order=1)
    return q

@pytest.mark.django_db
class TestOnboardingAPI:
    def test_fresh_user_can_create_socio_response_set(self, api_client, fresh_user, socio_questionnaire):
        api_client.force_authenticate(user=fresh_user)
        url = '/api/questionnaires/response-sets/'
        
        response = api_client.post(url, {'questionnaire': str(socio_questionnaire.id)})
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify the created response set status is DRAFT
        rs_id = response.data['id']
        rs = ResponseSet.objects.get(id=rs_id)
        assert rs.status == 'DRAFT'
        assert rs.user == fresh_user

    def test_onboarded_user_blocked_from_creating_socio_response_set(self, api_client, onboarded_user, socio_questionnaire):
        api_client.force_authenticate(user=onboarded_user)
        url = '/api/questionnaires/response-sets/'
        
        response = api_client.post(url, {'questionnaire': str(socio_questionnaire.id)})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already completed the sociodemographic assessment" in response.data['detail']

    def test_double_creation_returns_existing_draft(self, api_client, fresh_user, socio_questionnaire):
        api_client.force_authenticate(user=fresh_user)
        url = '/api/questionnaires/response-sets/'
        
        # Create first time
        res1 = api_client.post(url, {'questionnaire': str(socio_questionnaire.id)})
        assert res1.status_code == status.HTTP_201_CREATED
        
        # Try to create second time while still DRAFT
        res2 = api_client.post(url, {'questionnaire': str(socio_questionnaire.id)})
        assert res2.status_code == status.HTTP_200_OK
        assert res1.data['id'] == res2.data['id']

    def test_draft_updates_blocked_on_completed_response_set(self, api_client, fresh_user, socio_questionnaire):
        api_client.force_authenticate(user=fresh_user)
        
        rs = ResponseSet.objects.create(
            user=fresh_user,
            questionnaire=socio_questionnaire,
            status='COMPLETED',
            completed_at=timezone.now()
        )
        
        url = f'/api/questionnaires/response-sets/{rs.id}/draft/'
        payload = {"responses_data": []}
        
        # Saving draft should be blocked on completed response sets
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_submission_idempotent_on_completed_response_set(self, api_client, fresh_user, socio_questionnaire):
        api_client.force_authenticate(user=fresh_user)
        
        rs = ResponseSet.objects.create(
            user=fresh_user,
            questionnaire=socio_questionnaire,
            status='COMPLETED',
            completed_at=timezone.now()
        )
        
        url = f'/api/questionnaires/response-sets/{rs.id}/submit/'
        payload = {"responses_data": []}
        
        # Submitting an already completed response set should return 200 OK (idempotent submission)
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_200_OK
