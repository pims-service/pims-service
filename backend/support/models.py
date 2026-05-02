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
