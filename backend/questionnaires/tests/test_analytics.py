import pytest
import csv
import io
from django.urls import reverse
from rest_framework import status
from questionnaires.models import Questionnaire, Question, Option, ResponseSet, Response
from questionnaires.services import QuestionnaireExportService

@pytest.mark.django_db
class TestAnalyticsAndExport:

    @pytest.fixture
    def setup_data(self, admin_user, test_user):
        # 1. Create Questionnaire
        q = Questionnaire.objects.create(title="Test Q", is_active=True)
        
        # 2. Create Questions
        q1 = Question.objects.create(questionnaire=q, content="Q1 Choice", type='CHOICE', order=1)
        q2 = Question.objects.create(questionnaire=q, content="Q2 Text", type='TEXT', order=2)
        
        # 3. Create Options
        o1 = Option.objects.create(question=q1, label="Option A", numeric_value=10, order=1)
        o2 = Option.objects.create(question=q1, label="Option B", numeric_value=20, order=2)
        
        # 4. Create Response Sets (1 completed, 1 draft)
        rs_completed = ResponseSet.objects.create(user=test_user, questionnaire=q, status='COMPLETED')
        rs_draft = ResponseSet.objects.create(user=test_user, questionnaire=q, status='DRAFT')
        
        # 5. Create Responses
        Response.objects.create(response_set=rs_completed, question=q1, selected_option=o1)
        Response.objects.create(response_set=rs_completed, question=q2, text_value="Hello World")
        
        return {
            'q': q,
            'q1': q1,
            'q2': q2,
            'admin': admin_user,
            'user': test_user,
            'rs_completed': rs_completed
        }

    def test_export_service_pivoting(self, setup_data):
        """Verify that the service correctly pivots normalized data into wide format."""
        q_id = setup_data['q'].id
        headers, data = QuestionnaireExportService.get_wide_format_data(q_id)
        
        assert len(headers) > 0
        assert f"Q_{setup_data['q1'].id}" in headers
        assert f"Q_{setup_data['q2'].id}" in headers
        
        # Should only include COMPLETED response sets
        assert len(data) == 1
        
        row = data[0]
        # Check numeric value for CHOICE question
        q1_index = headers.index(f"Q_{setup_data['q1'].id}")
        assert row[q1_index] == 10
        
        # Check text value for TEXT question
        q2_index = headers.index(f"Q_{setup_data['q2'].id}")
        assert row[q2_index] == "Hello World"

    def test_export_view_permissions(self, api_client, setup_data):
        """Verify only admins can export data."""
        url = reverse('questionnaire_export', kwargs={'pk': setup_data['q'].id})
        
        # Non-admin user
        api_client.force_authenticate(user=setup_data['user'])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Admin user
        api_client.force_authenticate(user=setup_data['admin'])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'text/csv'

    def test_analytics_summary_view(self, api_client, setup_data):
        """Verify the analytics summary calculations."""
        url = reverse('questionnaire_analytics', kwargs={'pk': setup_data['q'].id})
        api_client.force_authenticate(user=setup_data['admin'])
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['total_starts'] == 2 # 1 completed + 1 draft
        assert data['total_completions'] == 1
        assert data['completion_rate_percentage'] == 50.0

    def test_export_streaming_content(self, api_client, setup_data):
        """Verify the actual CSV content streamed from the view."""
        url = reverse('questionnaire_export', kwargs={'pk': setup_data['q'].id})
        api_client.force_authenticate(user=setup_data['admin'])
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        # Consume streaming content
        content = b"".join(response.streaming_content).decode()
        csv_reader = csv.DictReader(io.StringIO(content))
        rows = list(csv_reader)
        
        assert len(rows) == 1
        q1_header = f"Q_{setup_data['q1'].id}"
        assert rows[0][q1_header] == "10"
        assert rows[0]['Username'] == setup_data['user'].username
