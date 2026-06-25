from django.db import models
from django.conf import settings

import uuid

class SupportTicket(models.Model):
    STATUS_CHOICES = (
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    )

    ticket_number = models.CharField(max_length=20, unique=True, blank=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    
    admin_reply = models.TextField(blank=True, null=True, help_text="Reply sent to the user")
    is_read_by_user = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True, null=True, help_text="Internal notes for admins")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Generate a unique ticket number like TKT-A1B2C3
            unique_id = uuid.uuid4().hex[:6].upper()
            self.ticket_number = f"TKT-{unique_id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_number} - {self.subject} ({self.status})"

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Count

def broadcast_ticket_counts(user):
    channel_layer = get_channel_layer()
    
    # 1. Notify the specific user about unread replies
    unread_count = SupportTicket.objects.filter(user=user, is_read_by_user=False).exclude(admin_reply__isnull=True).count()
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}",
        {
            "type": "update_ticket_count",
            "count": unread_count
        }
    )
    # Notify participant to reload ticket list
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}",
        {
            "type": "ticket_updated_event",
            "message": "reload"
        }
    )

    # 2. Notify all admins about open tickets and reload queries list
    from users.models import User
    open_count = SupportTicket.objects.filter(status='Open').count()
    admins = User.objects.filter(is_staff=True)
    for admin in admins:
        async_to_sync(channel_layer.group_send)(
            f"user_{admin.id}",
            {
                "type": "update_ticket_count",
                "count": open_count
            }
        )
        async_to_sync(channel_layer.group_send)(
            f"user_{admin.id}",
            {
                "type": "ticket_updated_event",
                "message": "reload"
            }
        )

@receiver(pre_save, sender=SupportTicket)
def cache_original_support_ticket_fields(sender, instance, **kwargs):
    if instance.id:
        try:
            original = SupportTicket.objects.get(pk=instance.id)
            instance._original_status = original.status
            instance._original_admin_reply = original.admin_reply
        except SupportTicket.DoesNotExist:
            instance._original_status = None
            instance._original_admin_reply = None
    else:
        instance._original_status = None
        instance._original_admin_reply = None

@receiver(post_save, sender=SupportTicket)
def ticket_updated(sender, instance, created, **kwargs):
    # Broadcast ticket counts via WebSockets
    broadcast_ticket_counts(instance.user)
    
    # Trigger email notifications
    if instance.subject and "call protocol" in instance.subject.lower():
        return

    from emails.tasks import (
        send_ticket_created_participant_email_task,
        send_ticket_created_admin_email_task,
        send_ticket_updated_participant_email_task,
    )
    from django.db import transaction

    if created:
        transaction.on_commit(lambda: send_ticket_created_participant_email_task.delay(instance.id))
        transaction.on_commit(lambda: send_ticket_created_admin_email_task.delay(instance.id))
    else:
        original_status = getattr(instance, '_original_status', None)
        original_reply = getattr(instance, '_original_admin_reply', None)

        status_changed = original_status is not None and instance.status != original_status
        reply_changed = original_reply is not None and instance.admin_reply != original_reply

        if status_changed or reply_changed:
            transaction.on_commit(lambda: send_ticket_updated_participant_email_task.delay(instance.id))

@receiver(post_delete, sender=SupportTicket)
def ticket_deleted(sender, instance, **kwargs):
    broadcast_ticket_counts(instance.user)

