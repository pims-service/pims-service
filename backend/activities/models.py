from django.db import models
from django.conf import settings
from phases.models import Phase

class Activity(models.Model):
    ACTIVITY_TYPES = (
        ('paragraph', 'Daily Paragraph'),
        ('task', 'Specific Task'),
        ('questionnaire', 'Questionnaire'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name='activities')
    group = models.ForeignKey('groups.Group', on_delete=models.CASCADE, null=True, blank=True, related_name='group_activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    day_number = models.PositiveIntegerField(null=True, blank=True, help_text="Sequence number for daily tasks")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Submission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='submissions')
    content = models.TextField()
    experiment_day = models.PositiveIntegerField(null=True, blank=True)
    submission_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.activity.title}"

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache

@receiver(post_save, sender=Submission)
def invalidate_user_completion_cache(sender, instance, **kwargs):
    """Clears the completion_rate cache for a user when they make a submission."""
    cache_key = f"user_{instance.user_id}_completion_rate"
    cache.delete(cache_key)
