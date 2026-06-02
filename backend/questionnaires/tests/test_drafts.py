import pytest
from django.urls import reverse
from rest_framework import status
from questionnaires.models import Questionnaire, ResponseSet, Question, Option, Response
from users.models import User

from rest_framework.test import APIClient

@pytest.mark.django_db
class TestDraftResponses:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', 
            password='password123',
            email='test@example.com'
        )
        self.questionnaire = Questionnaire.objects.create(
            title="Socio Demo", 
            assessment_type='SOCIODEMOGRAPHIC'
        )
        self.question1 = Question.objects.create(
            questionnaire=self.questionnaire, 
            content="Age?", 
            order=1, 
            type='CHOICE'
        )
        self.option1 = Option.objects.create(
            question=self.question1, 
            label="18-25", 
            order=1,
            numeric_value=0
        )
        self.question2 = Question.objects.create(
            questionnaire=self.questionnaire, 
            content="Gender?", 
            order=2, 
            type='CHOICE'
        )
        self.option2 = Option.objects.create(
            question=self.question2, 
            label="Male", 
            order=1,
            numeric_value=0
        )

    def test_save_draft_responses(self):
        self.client.force_authenticate(user=self.user)
        
        # 1. Create the response set
        rs = ResponseSet.objects.create(
            user=self.user,
            questionnaire=self.questionnaire,
            status='DRAFT'
        )
        
        url = reverse('response_set_save_draft', kwargs={'pk': rs.id})
        
        # 2. Save one draft response
        payload = {
            "responses_data": [
                {
                    "question_id": self.question1.id,
                    "selected_option_id": self.option1.id
                }
            ]
        }
        
        response = self.client.post(url, data=payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        rs.refresh_from_db()
        assert rs.status == 'DRAFT'
        assert rs.responses.count() == 1
        assert rs.responses.first().question == self.question1
        assert rs.responses.first().selected_option == self.option1
        
        # 3. Update the draft response with a second question
        payload_update = {
            "responses_data": [
                {
                    "question_id": self.question1.id,
                    "selected_option_id": self.option1.id
                },
                {
                    "question_id": self.question2.id,
                    "selected_option_id": self.option2.id
                }
            ]
        }
        
        response2 = self.client.post(url, data=payload_update, format='json')
        assert response2.status_code == status.HTTP_200_OK
        
        rs.refresh_from_db()
        assert rs.status == 'DRAFT'
        assert rs.responses.count() == 2
