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
    def test_baseline_csv_export_trigger_async(self, admin_client, normal_user, baseline_qs):
        ResponseSet.objects.create(user=normal_user, questionnaire=baseline_qs, status='COMPLETED')
        from admin_tools.models import ExportTask
        
        # Now uses POST to trigger
        response = admin_client.post(reverse('export_baseline_csv'), data={'group': 'All'})
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert 'task_id' in data
        
        # Verify task was created in DB
        task = ExportTask.objects.get(id=data['task_id'])
        assert task.user == admin_client.handler._force_user # verify authenticated user
        assert task.status == 'PENDING'

    def test_baseline_csv_export_group_filter_async(self, admin_client, normal_user, other_user, baseline_qs):
        from admin_tools.models import ExportTask
        ResponseSet.objects.create(user=normal_user, questionnaire=baseline_qs, status='COMPLETED')
        
        # Trigger with specific group filter in POST body
        response = admin_client.post(reverse('export_baseline_csv'), data={'group': normal_user.group.name})
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        task = ExportTask.objects.get(id=response.json()['task_id'])
        assert task.filters['group'] == normal_user.group.name

    def test_export_task_status_check(self, admin_client):
        from admin_tools.models import ExportTask
        task = ExportTask.objects.create(user=admin_client.handler._force_user, status='PROCESSING')
        
        url = reverse('export_task_status', kwargs={'task_id': task.id})
        response = admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'PROCESSING'
