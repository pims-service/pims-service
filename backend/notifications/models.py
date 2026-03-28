from django.db import models
from django.conf import settings

class Notification(models.Model):
    TYPES = (
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
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

    def __str__(self):
        return f"{self.user.username} - {self.n_type} - {self.status}"
