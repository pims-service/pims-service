import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
def test_admin_export_csv(admin_client, test_user):
    url = reverse('export_csv')
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response['Content-Type'] == 'text/csv'
    assert 'experiment_data_spss.csv' in response['Content-Disposition']
