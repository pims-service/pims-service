import pytest
from channels.testing import WebsocketCommunicator
from core.asgi import application
from notifications.models import Notification
from support.models import SupportTicket
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()

from asgiref.sync import sync_to_async

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_notification_websocket_authenticated():
    user = await sync_to_async(User.objects.create_user)(username="wsuser", email="ws@ex.com", password="pass")
    token = str(AccessToken.for_user(user))
    
    communicator = WebsocketCommunicator(application, f"/ws/notifications/?token={token}")
    connected, _ = await communicator.connect()
    assert connected
    
    # Trigger a notification push via signal
    await sync_to_async(Notification.objects.create)(
        user=user,
        title="WebSocket Test",
        message="Real-time check"
    )
    
    # Receive message
    response = await communicator.receive_json_from()
    assert response["type"] == "notification"
    assert response["data"]["title"] == "WebSocket Test"
    
    await communicator.disconnect()

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_notification_websocket_unauthenticated():
    communicator = WebsocketCommunicator(application, "/ws/notifications/?token=invalid")
    connected, _ = await communicator.connect()
    assert connected
    
    # Since user is Anonymous, they shouldn't receive notifications
    user = await sync_to_async(User.objects.create_user)(username="otheruser", email="o@ex.com", password="pass")
    await sync_to_async(Notification.objects.create)(
        user=user,
        title="Secret",
        message="Private"
    )
    
    # Check if we receive anything (we shouldn't)
    assert await communicator.receive_nothing()
        
    await communicator.disconnect()

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_support_ticket_count_push():
    user = await sync_to_async(User.objects.create_user)(username="ticketuser", email="t@ex.com", password="pass")
    token = str(AccessToken.for_user(user))
    
    communicator = WebsocketCommunicator(application, f"/ws/notifications/?token={token}")
    await communicator.connect()
    
    # Create a ticket
    ticket = await sync_to_async(SupportTicket.objects.create)(
        user=user,
        subject="Help",
        message="Issue"
    )
    
    # Receive initial count (created)
    response = await communicator.receive_json_from()
    assert "ticket_count" in response["data"]
    
    # Update ticket (admin reply)
    ticket.admin_reply = "Resolved"
    ticket.is_read_by_user = False
    await sync_to_async(ticket.save)()
    
    response = await communicator.receive_json_from()
    assert response["type"] == "ticket_count"
    
    await communicator.disconnect()
