import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User
from questionnaires.models import Questionnaire, Question, ResponseSet, Option, Response
from groups.models import Group
import csv
import io

@pytest.fixture
def normal_user(db, test_group):
    user = User.objects.create_user(username='participant', email='p@b.com', password='pw')
    user.group = test_group
    user.save()
    return user

@pytest.fixture
def other_user(db):
    user = User.objects.create_user(username='other', email='other@b.com', password='pw')
    return user

@pytest.fixture
def baseline_qs(db):
    qs = Questionnaire.objects.create(title='Baseline', is_baseline=True)
    Question.objects.create(questionnaire=qs, content='Age?', type='TEXT', order=1)
    q2 = Question.objects.create(questionnaire=qs, content='Color?', type='CHOICE', order=2)
    Option.objects.create(question=q2, label='Red', numeric_value=1)
    return qs

@pytest.mark.django_db
class TestDashboardAnalytics:
    def test_dashboard_analytics_auth(self, api_client, normal_user):
        api_client.force_authenticate(user=normal_user)
        response = api_client.get(reverse('dashboard_analytics'))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_dashboard_analytics_data(self, admin_client, normal_user, baseline_qs):
        ResponseSet.objects.create(user=normal_user, questionnaire=baseline_qs, status='COMPLETED')
        
        response = admin_client.get(reverse('dashboard_analytics'))
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['total_participants'] >= 1
        assert data['total_submissions'] >= 1
        assert 'active_rate_percentage' in data

@pytest.mark.django_db
class TestBaselineCSVExport:
    def test_baseline_csv_export_wide_format(self, admin_client, normal_user, baseline_qs):
        rs = ResponseSet.objects.create(user=normal_user, questionnaire=baseline_qs, status='COMPLETED')
        q1 = baseline_qs.questions.get(order=1)
        q2 = baseline_qs.questions.get(order=2)
        opt_red = q2.options.filter(label='Red').first()
        
        Response.objects.create(response_set=rs, question=q1, text_value='25')
        Response.objects.create(response_set=rs, question=q2, selected_option=opt_red)
        
        response = admin_client.get(reverse('export_baseline_csv'))
        
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'text/csv'
        
        csv_file = io.StringIO(response.content.decode('utf-8'))
        reader = csv.reader(csv_file)
        rows = list(reader)
        
        assert len(rows) == 2 # Header + 1 Participant row
        
        # Validate Headers (Wide Format structure)
        headers = rows[0]
        assert headers[:5] == ['ParticipantID', 'Username', 'Group', 'StartedAt', 'CompletedAt']
        assert headers[5] == 'Question 1'
        assert headers[6] == 'Question 2'
        
        # Validate Data Row
        data_row = rows[1]
        assert data_row[1] == 'participant'
        assert data_row[5] == '25'
        assert data_row[6] == 'Red'

    def test_baseline_csv_export_group_filter(self, admin_client, normal_user, other_user, baseline_qs):
        ResponseSet.objects.create(user=normal_user, questionnaire=baseline_qs, status='COMPLETED')
        ResponseSet.objects.create(user=other_user, questionnaire=baseline_qs, status='COMPLETED')
        
        # Apply group filter in query param mapped exactly to normal_user's group
        response = admin_client.get(reverse('export_baseline_csv') + f'?group={normal_user.group.name}')
        
        assert response.status_code == status.HTTP_200_OK
        csv_file = io.StringIO(response.content.decode('utf-8'))
        reader = csv.reader(csv_file)
        rows = list(reader)
        
        # The filter should return only the participant from the specific group
        assert len(rows) == 2 
        assert rows[1][1] == 'participant'
