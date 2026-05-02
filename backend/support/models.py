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

from django.db.models.signals import post_save, post_delete
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

    # 2. Notify all admins about open tickets
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

@receiver(post_save, sender=SupportTicket)
def ticket_updated(sender, instance, **kwargs):
    broadcast_ticket_counts(instance.user)

@receiver(post_delete, sender=SupportTicket)
def ticket_deleted(sender, instance, **kwargs):
    broadcast_ticket_counts(instance.user)
