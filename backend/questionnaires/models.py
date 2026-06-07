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
    is_posttest = models.BooleanField(default=False, help_text="Defines if this questionnaire is the Day 7 post-test reassessment")
    ASSESSMENT_TYPES = (
        ('SOCIODEMOGRAPHIC', 'Sociodemographic Form'),
        ('PSYCHOMETRIC', 'Psychometric Battery'),
    )
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES, default='PSYCHOMETRIC')
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
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.SET_NULL, null=True, blank=True, related_name='attempts')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    MILESTONES = (
        ('SIGNUP', 'Signup Baseline'),
        ('7_DAYS', '7 Days Post-Test'),
        ('3_MONTHS', '3 Months'),
        ('6_MONTHS', '6 Months'),
        ('1_YEAR', '1 Year'),
        ('90_DAYS', '90 Days'),
    )
    milestone = models.CharField(max_length=15, choices=MILESTONES, db_index=True, null=True, blank=True)
    scores = models.JSONField(default=dict, blank=True, help_text="Calculated subscale and total scores on submission")
    suicide_risk_triggered = models.BooleanField(default=False)
    suicide_risk_opt_in = models.BooleanField(null=True, blank=True)

    class Meta:
        indexes = [
            # Speeds up: admin analytics queries filtering by status+date
            models.Index(fields=['status', 'completed_at'], name='idx_rs_status_completed'),
            # Speeds up: participant dashboard loading their own responses
            models.Index(fields=['user', 'status'], name='idx_rs_user_status'),
            # Speeds up: querying user progress by milestone
            models.Index(fields=['user', 'milestone', 'status'], name='idx_rs_user_milestone_status'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['user', 'questionnaire', 'milestone'], name='unique_user_questionnaire_milestone')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.questionnaire.title if self.questionnaire else 'Deleted Questionnaire'} ({self.status})"

class Response(models.Model):
    """
    A single answer within a response set.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    response_set = models.ForeignKey(ResponseSet, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True, blank=True)
    selected_option = models.ForeignKey(Option, on_delete=models.SET_NULL, null=True, blank=True)
    text_value = models.TextField(null=True, blank=True)
    
    # Denormalized fields to preserve answer history if questions/options are edited/deleted
    question_text = models.TextField(null=True, blank=True)
    question_order = models.PositiveIntegerField(null=True, blank=True)
    selected_option_value = models.IntegerField(null=True, blank=True)
    selected_option_label = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['response_set', 'question'], name='unique_response_per_question')
        ]

    def __str__(self):
        return f"Response to {self.question.id} in {self.response_set.id}"
