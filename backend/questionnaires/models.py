import uuid
from django.db import models
from django.conf import settings

class Questionnaire(models.Model):
    """
    Represents a full questionnaire instance.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_baseline = models.BooleanField(default=False, help_text="Defines if this questionnaire is the initial screening for group assignment")
    max_completion_time = models.DurationField(null=True, blank=True, help_text="Maximum allowed time to complete the questionnaire")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({'Active' if self.is_active else 'Inactive'})"

class Question(models.Model):
    """
    An individual question within a questionnaire.
    """
    QUESTION_TYPES = (
        ('CHOICE', 'Multiple Choice'),
        ('SCALE', 'Likert Scale / Discrete Scale'),
        ('TEXT', 'Open Text'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='questions')
    content = models.TextField()
    type = models.CharField(max_length=10, choices=QUESTION_TYPES)
    order = models.PositiveIntegerField(default=0)
    required = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"[{self.type}] {self.content[:50]}"

class Option(models.Model):
    """
    Predefined options for CHOICE and SCALE questions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    label = models.CharField(max_length=200)
    numeric_value = models.IntegerField(help_text="Numeric value for statistical analysis (SPSS compatible)")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.label} ({self.numeric_value})"

class ResponseSet(models.Model):
    """
    A specific attempt at a questionnaire by a user.
    """
    STATUS_CHOICES = (
        ('DRAFT', 'In Progress'),
        ('COMPLETED', 'Completed'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='response_sets')
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='attempts')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.questionnaire.title} ({self.status})"

class Response(models.Model):
    """
    A single answer within a response set.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    response_set = models.ForeignKey(ResponseSet, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.SET_NULL, null=True, blank=True)
    text_value = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Response to {self.question.id} in {self.response_set.id}"
