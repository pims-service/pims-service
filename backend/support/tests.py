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
    # Call Protocol ticket (should be excluded from standard list)
    SupportTicket.objects.create(user=participant_user, subject='Call Protocol: High daily activity miss', message='Requires follow-up call')
    
    response = admin_client.get('/api/support/tickets/')
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
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
    # Call Protocol ticket (should be excluded from standard open_count)
    SupportTicket.objects.create(user=participant_user, subject='Call Protocol: Assessment Overdue', message='Call required', status='Open')
    
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


@pytest.mark.django_db
def test_admin_can_access_follow_ups(admin_client, participant_user):
    # 1. Create a ticket under Call Protocol
    t1 = SupportTicket.objects.create(
        user=participant_user,
        subject='Call Protocol: High Daily Activity Miss Rate (Tier 3)',
        message='Requires follow-up call'
    )
    # 2. Create a generic support ticket
    t2 = SupportTicket.objects.create(
        user=participant_user,
        subject='Login Issue',
        message='General login issue'
    )

    response = admin_client.get('/api/support/tickets/follow_ups/')
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    results = data.get('results', data) if isinstance(data, dict) else data

    # Verify only the Call Protocol ticket is returned
    assert len(results) == 1
    assert results[0]['subject'] == 'Call Protocol: High Daily Activity Miss Rate (Tier 3)'
    assert results[0]['user_whatsapp_number'] == participant_user.whatsapp_number


@pytest.mark.django_db
def test_participant_cannot_access_follow_ups(auth_client):
    response = auth_client.get('/api/support/tickets/follow_ups/')
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_admin_can_filter_follow_ups(admin_client, participant_user):
    # Create tickets with different statuses
    SupportTicket.objects.create(
        user=participant_user,
        subject='Call Protocol: Task 1',
        message='Msg1',
        status='Open'
    )
    SupportTicket.objects.create(
        user=participant_user,
        subject='Call Protocol: Task 2',
        message='Msg2',
        status='In Progress'
    )
    SupportTicket.objects.create(
        user=participant_user,
        subject='Call Protocol: Task 3',
        message='Msg3',
        status='Resolved'
    )

    # Filter: Open
    res_open = admin_client.get('/api/support/tickets/follow_ups/?status=Open')
    assert res_open.status_code == status.HTTP_200_OK
    data = res_open.json()
    results = data.get('results', data) if isinstance(data, dict) else data
    assert len(results) == 1
    assert results[0]['subject'] == 'Call Protocol: Task 1'

    # Filter: In Progress
    res_ip = admin_client.get('/api/support/tickets/follow_ups/?status=in_progress')
    assert res_ip.status_code == status.HTTP_200_OK
    data = res_ip.json()
    results = data.get('results', data) if isinstance(data, dict) else data
    assert len(results) == 1
    assert results[0]['subject'] == 'Call Protocol: Task 2'

    # Filter: Resolved
    res_res = admin_client.get('/api/support/tickets/follow_ups/?status=resolved')
    assert res_res.status_code == status.HTTP_200_OK
    data = res_res.json()
    results = data.get('results', data) if isinstance(data, dict) else data
    assert len(results) == 1
    assert results[0]['subject'] == 'Call Protocol: Task 3'


from django.core import mail
from django.conf import settings

@pytest.mark.django_db(transaction=True)
def test_support_ticket_creation_sends_emails(participant_user):
    mail.outbox.clear()
    
    # 1. Create a support ticket
    ticket = SupportTicket.objects.create(
        user=participant_user,
        subject="Login Issues",
        message="I cannot login to my account."
    )
    
    # 2. Check emails sent (1 to participant, 1 to admin)
    assert len(mail.outbox) == 2
    
    # Participant confirmation email
    participant_email = next(m for m in mail.outbox if participant_user.email in m.to)
    assert "We have received your support request" in participant_email.subject
    assert "ہمیں آپ کی مدد کی درخواست موصول ہو گئی ہے" in participant_email.subject
    assert ticket.ticket_number in participant_email.subject
    assert "Login Issues" in participant_email.body
    
    # Admin alert email
    admin_email = next(m for m in mail.outbox if settings.SUPPORT_ADMIN_EMAIL in m.to)
    assert f"New Support Ticket Raised: {ticket.ticket_number}" in admin_email.subject
    assert ticket.message in admin_email.body
    assert participant_user.email in admin_email.body


@pytest.mark.django_db(transaction=True)
def test_call_protocol_creation_skips_emails(participant_user):
    mail.outbox.clear()
    
    # Create Call Protocol ticket
    SupportTicket.objects.create(
        user=participant_user,
        subject="Call Protocol: High daily activity miss",
        message="Engagement check required."
    )
    
    # Should not trigger any emails
    assert len(mail.outbox) == 0


@pytest.mark.django_db(transaction=True)
def test_support_ticket_update_sends_emails(participant_user):
    # Setup: Create ticket first
    ticket = SupportTicket.objects.create(
        user=participant_user,
        subject="General Query",
        message="Hello team"
    )
    mail.outbox.clear()
    
    # 1. Update status
    ticket.status = "In Progress"
    ticket.save()
    
    assert len(mail.outbox) == 1
    msg = mail.outbox[0]
    assert msg.to == [participant_user.email]
    assert "Support Ticket Update" in msg.subject
    assert "سائیکیورسٹی سپورٹ ٹکٹ کی معلومات" in msg.subject
    assert "In Progress" in msg.body
    assert "کام جاری ہے" in msg.body
    assert "View Support Tickets" in msg.body
    assert "support=true" in msg.body


@pytest.mark.django_db(transaction=True)
def test_support_ticket_update_reply_sends_emails(participant_user):
    ticket = SupportTicket.objects.create(
        user=participant_user,
        subject="General Query",
        message="Hello team"
    )
    mail.outbox.clear()
    
    # 2. Update status and reply
    ticket.status = "Resolved"
    ticket.admin_reply = "We have resolved this issue. Try again now!"
    ticket.save()
    
    assert len(mail.outbox) == 1
    msg = mail.outbox[0]
    assert msg.to == [participant_user.email]
    assert "Resolved" in msg.body
    assert "We have resolved this issue" in msg.body


@pytest.mark.django_db(transaction=True)
def test_support_ticket_update_internal_notes_skips_emails(participant_user):
    ticket = SupportTicket.objects.create(
        user=participant_user,
        subject="General Query",
        message="Hello team"
    )
    mail.outbox.clear()
    
    # Update internal admin_notes only
    ticket.admin_notes = "Internal notes that participant should not see"
    ticket.save()
    
    # Should not send any email updates to the participant
    assert len(mail.outbox) == 0


