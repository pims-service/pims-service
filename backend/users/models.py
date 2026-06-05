from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.cache import cache
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
    date_of_birth = models.DateField(null=True, blank=True)
    
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

    @property
    def display_name(self):
        """Returns the full name if present, otherwise capitalizes the username."""
        if self.full_name:
            return self.full_name
        # Format username: replace dots with space and capitalize (e.g. sarah.kim -> Sarah Kim)
        name_part = self.username.replace('.', ' ').replace('_', ' ')
        return name_part.title()

    # Onboarding state
    has_completed_sociodemographic = models.BooleanField(default=False)
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)

    # Post-test state (Day 7 reassessment)
    has_completed_posttest = models.BooleanField(default=False)
    posttest_completed_at = models.DateTimeField(null=True, blank=True)
    # T2 follow‑up state (90‑day assessment)
    has_completed_t2 = models.BooleanField(default=False)
    t2_completed_at = models.DateTimeField(null=True, blank=True)  # Original consents (migrated/supported for now)
    email_consent = models.BooleanField(default=False)
    whatsapp_consent = models.BooleanField(default=False)
    
    # Disqualification state
    is_disqualified = models.BooleanField(default=False)
    disqualification_reason = models.TextField(blank=True)
    
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    @property
    def current_experiment_day(self):
        """
        Calculates the user's current day in the experiment (1-indexed).
        Caches the result in Redis until next midnight to optimize speed.
        """
        if getattr(self, 'is_disqualified', False):
            return None

        if not self.onboarding_completed_at:
            return None

        cache_key = f"user_{self.user_id}_exp_day"
        cached_day = cache.get(cache_key)
        if cached_day is not None:
            return cached_day

        now = timezone.now()
        # Calculate days since onboarding completion
        delta = timezone.localdate() - timezone.localtime(self.onboarding_completed_at).date()
        exp_day = delta.days + 1

        # Cache until midnight
        tomorrow = (now + timezone.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_until_midnight = int((tomorrow - now).total_seconds())
        if seconds_until_midnight > 0:
            cache.set(cache_key, exp_day, timeout=seconds_until_midnight)

        return exp_day

    @property
    def is_posttest_due(self):
        """Returns True if the user has reached Day 8+ (7 days after onboarding completion) and hasn't completed the post-test."""
        if not self.has_completed_sociodemographic or self.has_completed_posttest:
            return False
        return self.current_experiment_day is not None and self.current_experiment_day >= 8

    @property
    def is_t2_due(self):
        """Returns True if the user is 90 days past onboarding and hasn't completed T2."""
        if not self.onboarding_completed_at or self.has_completed_t2:
            return False
        now = timezone.now()
        days_since_onboarding = (now.date() - self.onboarding_completed_at.date()).days
        return days_since_onboarding >= 90

    @property
    def get_due_milestone(self):
        """
        Calculates and returns the user's currently due assessment milestone:
        'SIGNUP', '7_DAYS', '3_MONTHS', '6_MONTHS', '1_YEAR', or None.
        Caches the result in Redis until next midnight to optimize speed.
        """
        cache_key = f"user_{self.user_id}_due_milestone"
        cached_val = cache.get(cache_key)
        if cached_val is not None:
            return None if cached_val == "NONE" else cached_val

        # Fetch completed milestones to prevent double-serving
        from questionnaires.models import ResponseSet
        completed_milestones = set(
            ResponseSet.objects.filter(user=self, status='COMPLETED', milestone__isnull=False)
            .values_list('milestone', flat=True)
        )
        if self.has_completed_posttest:
            completed_milestones.add('7_DAYS')

        # If onboarding is incomplete, SIGNUP is due.
        if not self.has_completed_sociodemographic or ('SIGNUP' not in completed_milestones and not self.onboarding_completed_at):
            return 'SIGNUP'

        if not self.onboarding_completed_at:
            return None

        now = timezone.now()
        due = None

        # Evaluate timeline sequentially
        if '7_DAYS' not in completed_milestones:
            if self.current_experiment_day is not None and self.current_experiment_day >= 8:
                due = '7_DAYS'
        else:
            # Find T1 completion time
            t1_completed_at = self.posttest_completed_at
            if not t1_completed_at:
                t1_rs = ResponseSet.objects.filter(user=self, status='COMPLETED', milestone='7_DAYS').first()
                if t1_rs:
                    t1_completed_at = t1_rs.completed_at
            
            if t1_completed_at:
                days_since_t1 = (now.date() - t1_completed_at.date()).days
                if '3_MONTHS' not in completed_milestones and days_since_t1 >= 90:
                    due = '3_MONTHS'
                elif '6_MONTHS' not in completed_milestones and days_since_t1 >= 180:
                    due = '6_MONTHS'
                elif '1_YEAR' not in completed_milestones and days_since_t1 >= 365:
                    due = '1_YEAR'

        # Cache until midnight
        tomorrow = (now + timezone.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_until_midnight = int((tomorrow - now).total_seconds())
        if seconds_until_midnight > 0:
            cache.set(cache_key, due if due is not None else "NONE", timeout=seconds_until_midnight)

        return due

    @property
    def completion_rate(self):
        """
        Calculates the percentage of daily activities completed relative to current day.
        Caches result for 5 minutes to prevent heavy DB hits on every dashboard refresh.
        """
        current_day = self.current_experiment_day
        if not current_day:
            return 0
        
        cache_key = f"user_{self.user_id}_completion_rate"
        cached_rate = cache.get(cache_key)
        if cached_rate is not None:
            return cached_rate

        # Max out at 7 days for calculation
        effective_day = min(current_day, 7)
        
        from activities.models import Submission
        submissions_count = Submission.objects.filter(user=self).values('experiment_day').distinct().count()
        
        # Avoid division by zero
        rate = int((submissions_count / effective_day) * 100) if effective_day > 0 else 0
        final_rate = min(rate, 100)
        
        # Cache for 5 minutes
        cache.set(cache_key, final_rate, timeout=300)
        
        return final_rate

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

class EmailVerificationOTP(models.Model):
    """
    Temporary storage for email verification OTCs (One-Time Codes).
    """
    email = models.EmailField(db_index=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_valid(self):
        from datetime import timedelta
        # Valid for 10 minutes
        return timezone.now() < self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"{self.email} - {self.otp} (Verified: {self.is_verified})"
