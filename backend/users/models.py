from django.contrib.auth.models import AbstractUser
from django.db import models
from groups.models import Group
from django.utils import timezone

class Role(models.Model):
    """
    Role associated with a user in the experiment platform.
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    """
    Custom user model for the experiment platform.
    """
    user_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(unique=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    
    # New Role ForeignKey
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    
    # Preserved existing fields
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='participants')
    traits = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def id(self):
        return self.user_id
    
    # Original consents (migrated/supported for now)
    email_consent = models.BooleanField(default=False)
    whatsapp_consent = models.BooleanField(default=False)
    
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

class UserConsent(models.Model):
    """
    Detailed consent record for a specific user.
    """
    consent_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consents')
    agreed = models.BooleanField(default=False)
    agreed_at = models.DateTimeField(default=timezone.now)
    consent_version = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.user.username} - v{self.consent_version} ({self.agreed})"
