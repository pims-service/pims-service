import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from users.models import Role
from .models import SupportTicket

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def participant_user():
    role, _ = Role.objects.get_or_create(name='Participant')
    return User.objects.create_user(
        email='participant@test.com',
        username='participant',
        password='password123',
        role=role
    )

@pytest.fixture
def admin_user():
    role, _ = Role.objects.get_or_create(name='Admin')
    user = User.objects.create_user(
        email='admin@test.com',
        username='admin',
        password='password123',
        role=role
    )
    user.is_staff = True
    user.save()
    return user

@pytest.fixture
def auth_client(api_client, participant_user):
    api_client.force_authenticate(user=participant_user)
    return api_client

@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client

@pytest.mark.django_db
def test_create_ticket_authenticated(auth_client, participant_user):
    data = {
        'subject': 'Help with login',
        'message': 'I cannot log in from my phone.'
    }
    response = auth_client.post('/api/support/tickets/', data)
    assert response.status_code == status.HTTP_201_CREATED
    assert SupportTicket.objects.count() == 1
    ticket = SupportTicket.objects.first()
    assert ticket.user == participant_user
    assert ticket.subject == 'Help with login'
    assert ticket.status == 'Open'

@pytest.mark.django_db
def test_create_ticket_unauthenticated(api_client):
    data = {
        'subject': 'Help with login',
        'message': 'I cannot log in from my phone.'
    }
    response = api_client.post('/api/support/tickets/', data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert SupportTicket.objects.count() == 0

@pytest.mark.django_db
def test_participant_can_list_own_tickets(auth_client, participant_user):
    SupportTicket.objects.create(user=participant_user, subject='Test', message='Msg')
    response = auth_client.get('/api/support/tickets/')
    # Participants can list their own tickets
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    results = data.get('results', data) if isinstance(data, dict) else data
    assert len(results) == 1
    assert results[0]['subject'] == 'Test'

@pytest.mark.django_db
def test_admin_can_list_tickets(admin_client, participant_user):
    SupportTicket.objects.create(user=participant_user, subject='Test', message='Msg')
    response = admin_client.get('/api/support/tickets/')
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # DRF could use pagination
    results = data.get('results', data) if isinstance(data, dict) else data
    assert len(results) == 1
    assert results[0]['subject'] == 'Test'

@pytest.mark.django_db
def test_admin_can_update_ticket(admin_client, participant_user):
    ticket = SupportTicket.objects.create(user=participant_user, subject='Test', message='Msg')
    data = {
        'status': 'Resolved',
        'admin_notes': 'Fixed the issue.',
        'admin_reply': 'We have fixed this for you.'
    }
    response = admin_client.patch(f'/api/support/tickets/{ticket.id}/', data)
    assert response.status_code == status.HTTP_200_OK
    ticket.refresh_from_db()
    assert ticket.status == 'Resolved'
    assert ticket.admin_notes == 'Fixed the issue.'
    assert ticket.admin_reply == 'We have fixed this for you.'

@pytest.mark.django_db
def test_admin_cannot_update_subject(admin_client, participant_user):
    ticket = SupportTicket.objects.create(user=participant_user, subject='Test', message='Msg')
    data = {
        'subject': 'Changed Subject'
    }
    response = admin_client.patch(f'/api/support/tickets/{ticket.id}/', data)
    assert response.status_code == status.HTTP_200_OK
    ticket.refresh_from_db()
    # Subject should be read_only for admin
    assert ticket.subject == 'Test'

@pytest.mark.django_db
def test_unread_count(auth_client, participant_user):
    # Ticket with no reply
    SupportTicket.objects.create(user=participant_user, subject='Test1', message='Msg1')
    # Ticket with reply, unread
    SupportTicket.objects.create(user=participant_user, subject='Test2', message='Msg2', admin_reply='Reply2', is_read_by_user=False)
    # Ticket with reply, read
    SupportTicket.objects.create(user=participant_user, subject='Test3', message='Msg3', admin_reply='Reply3', is_read_by_user=True)
    
    response = auth_client.get('/api/support/tickets/unread_count/')
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['count'] == 1

@pytest.mark.django_db
def test_open_count(admin_client, participant_user):
    SupportTicket.objects.create(user=participant_user, subject='Test1', message='Msg1', status='Open')
    SupportTicket.objects.create(user=participant_user, subject='Test2', message='Msg2', status='In Progress')
    SupportTicket.objects.create(user=participant_user, subject='Test3', message='Msg3', status='Resolved')
    
    response = admin_client.get('/api/support/tickets/open_count/')
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['count'] == 2

@pytest.mark.django_db
def test_mark_read(auth_client, participant_user):
    ticket = SupportTicket.objects.create(user=participant_user, subject='Test', message='Msg', admin_reply='Reply', is_read_by_user=False)
    response = auth_client.post(f'/api/support/tickets/{ticket.id}/mark_read/')
    assert response.status_code == status.HTTP_200_OK
    ticket.refresh_from_db()
    assert ticket.is_read_by_user is True
