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
    entry_1 = models.TextField(blank=True, default='')
    entry_2 = models.TextField(blank=True, default='')
    entry_3 = models.TextField(blank=True, default='')
    experiment_day = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    submission_date = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'experiment_day'],
                name='unique_user_experiment_day'
            )
        ]
        indexes = [
            # Speeds up: "Did this user submit today?" — the most frequent query
            models.Index(fields=['user', 'submission_date'], name='idx_submission_user_date'),
        ]

    def save(self, *args, **kwargs):
        # Automatically update content by joining entry_1, entry_2, entry_3
        # If entry_1, entry_2, entry_3 are not provided but content is (e.g. legacy tests), keep content as is
        if self.entry_1 or self.entry_2 or self.entry_3:
            self.content = f"{self.entry_1}\n\n---\n\n{self.entry_2}\n\n---\n\n{self.entry_3}"
        super().save(*args, **kwargs)

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
