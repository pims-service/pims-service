from django.db import models
from django.conf import settings

class Questionnaire(models.Model):
    TYPES = (
        ('pre', 'Pre-Experiment'),
        ('post', 'Post-Experiment'),
        ('daily', 'Daily Assessment'),
    )
    title = models.CharField(max_length=200)
    q_type = models.CharField(max_length=10, choices=TYPES)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_q_type_display()} - {self.title}"

class QuestionnaireResponse(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='q_responses')
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='responses')
    responses = models.JSONField() # Store answers as a JSON object
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'questionnaire')

    def __str__(self):
        return f"{self.user.username} - {self.questionnaire.title}"
