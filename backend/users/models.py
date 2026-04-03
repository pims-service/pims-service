from django.contrib.auth.models import AbstractUser
from django.db import models
from groups.models import Group

class User(AbstractUser):
    email = models.EmailField(unique=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    email_consent = models.BooleanField(default=False)
    whatsapp_consent = models.BooleanField(default=False)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='participants')
    traits = models.JSONField(default=dict, blank=True)
    registration_date = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
