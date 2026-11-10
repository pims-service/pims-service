from django.db import models
from django.conf import settings


class ManualEmailCampaign(models.Model):
    """One admin-sent email (to a group of participants, or a test to the admin)."""
    SEGMENTS = (
        ('not_started', 'Not started'),
        ('stopped', 'Stopped'),
        ('d7_due', '7-day due'),
        ('all_eligible', 'All eligible'),
        ('manual', 'Picked by hand'),
        ('test', 'Test to admin'),
    )
    STATUS = (
        ('queued', 'Queued'),
        ('sending', 'Sending'),
        ('done', 'Done'),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='manual_email_campaigns'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    segment = models.CharField(max_length=20, choices=SEGMENTS)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    recipient_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS, default='queued')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_segment_display()} - {self.subject}"


class Notification(models.Model):
    TYPES = (
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('sms', 'SMS'),
    )
    STATUS = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    n_type = models.CharField(max_length=10, choices=TYPES)
    message = models.TextField()
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    # Set for admin-sent (manual) emails; these are not pushed to the in-app notification feed.
    campaign = models.ForeignKey(
        ManualEmailCampaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications'
    )

    def __str__(self):
        return f"{self.user.username} - {self.n_type} - {self.status}"

from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=Notification)
def send_notification_realtime(sender, instance, created, **kwargs):
    if created and instance.campaign_id is None:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{instance.user.id}",
            {
                "type": "send_notification",
                "message": instance.message,
                "n_type": instance.n_type,
            }
        )
