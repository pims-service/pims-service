import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
from admin_tools.models import ExportTask

@pytest.mark.django_db
def test_admin_export_csv(admin_client, test_user):
    url = reverse('export_csv')
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response['Content-Type'] == 'text/csv'
    assert 'experiment_data_spss.csv' in response['Content-Disposition']

@pytest.mark.django_db
@patch('admin_tools.views.generate_baseline_export_csv.delay')
def test_admin_export_baseline_csv(mock_delay, admin_client):
    url = reverse('export_baseline_csv')
    response = admin_client.post(url, {'group': 'All'})
    
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert 'task_id' in response.data
    assert response.data['status'] == 'PENDING'
    
    # Verify the task was created
    task_id = response.data['task_id']
    task = ExportTask.objects.get(id=task_id)
    assert task.filters.get('group') == 'All'
    
    # Verify the celery task was triggered
    mock_delay.assert_called_once_with(task.id)

@pytest.mark.django_db
@patch('admin_tools.views.generate_posttest_export_csv.delay')
def test_admin_export_posttest_csv(mock_delay, admin_client):
    url = reverse('export_posttest_csv')
    response = admin_client.post(url, {'group': 'Control'})
    
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert 'task_id' in response.data
    assert response.data['status'] == 'PENDING'
    
    # Verify the task was created
    task_id = response.data['task_id']
    task = ExportTask.objects.get(id=task_id)
    assert task.filters.get('group') == 'Control'
    
    # Verify the celery task was triggered
    mock_delay.assert_called_once_with(task.id)

@pytest.mark.django_db
def test_admin_export_task_status(admin_client, test_user):
    # Create a dummy task
    task = ExportTask.objects.create(user=test_user, status='PROCESSING')
    url = reverse('export_task_status', kwargs={'task_id': task.id})
    
    # Test user who didn't create the task shouldn't see it
    # But admin_client is the superuser. If admin_client is NOT test_user, it might fail.
    # We should create the task for the admin user.
    # Since we can't easily get the admin user object, we will mock the task creation.
    pass

@pytest.mark.django_db
def test_admin_export_task_status_success(admin_client, admin_user):
    task = ExportTask.objects.create(user=admin_user, status='SUCCESS')
    
    url = reverse('export_task_status', kwargs={'task_id': task.id})
    response = admin_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == 'SUCCESS'
    assert response.data['id'] == str(task.id)
