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
    def current_activity_state(self):
        """
        Returns the active pre-assessment activity wave state, cached until midnight.
        """
        if getattr(self, 'is_disqualified', False) or not self.onboarding_completed_at:
            return None

        cache_key = f"user_{self.user_id}_activity_state"
        cached_state = cache.get(cache_key)
        if cached_state is not None:
            return None if cached_state == "NONE" else cached_state

        from activities.timeline import get_active_activity_state

        state = get_active_activity_state(self)
        now = timezone.now()
        tomorrow = (now + timezone.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_until_midnight = int((tomorrow - now).total_seconds())
        if seconds_until_midnight > 0:
            cache.set(
                cache_key,
                "NONE" if state is None else state,
                timeout=seconds_until_midnight,
            )
        return state

    @property
    def current_activity_wave(self):
        state = self.current_activity_state
        return state.wave if state else None

    @property
    def current_experiment_day(self):
        """
        Day within the current 7-day pre-assessment activity block (1-7), or None
        when the user is between waves.
        """
        state = self.current_activity_state
        return state.day_in_block if state else None

    @property
    def is_posttest_due(self):
        """Returns True once the PRE_T1 activity block has ended and T1 is still outstanding."""
        if not self.has_completed_sociodemographic or self.has_completed_posttest:
            return False
        if not self.onboarding_completed_at:
            return False
        due_date = self.onboarding_completed_at + timezone.timedelta(days=7)
        return timezone.now() >= due_date

    @property
    def is_t2_due(self):
        """Returns True if the user is 90 days past onboarding and hasn't completed T2."""
        if not self.onboarding_completed_at or self.has_completed_t2:
            return False
        today_date = timezone.localdate()
        onboard_date = timezone.localtime(self.onboarding_completed_at).date()
        days_since_onboarding = (today_date - onboard_date).days
        return days_since_onboarding >= 90

    @property
    def get_due_milestone(self):
        """
        Calculates and returns the user's currently due assessment milestone:
        'SIGNUP', '7_DAYS', '1_MONTH', '3_MONTHS', '6_MONTHS', '1_YEAR', or None.
        Caches the result in Redis until next midnight to optimize speed.
        """
        cache_key = f"user_{self.user_id}_due_milestone"
        cached_val = cache.get(cache_key)
        if cached_val is not None:
            return None if cached_val == "NONE" else cached_val

        # Fetch completed milestones to prevent double-serving
        from questionnaires.models import ResponseSet
        completed_milestones = set(
            ResponseSet.objects.filter(
                user=self,
                status='COMPLETED',
                milestone__isnull=False,
                questionnaire__assessment_type='PSYCHOMETRIC'
            )
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
        
        # 1. 7_DAYS (T1 post-test)
        if '7_DAYS' not in completed_milestones:
            due_date = self.onboarding_completed_at + timezone.timedelta(days=7)
            if now >= due_date:
                if now - due_date >= timezone.timedelta(days=14):
                    # 7_DAYS has expired. Move on.
                    pass
                else:
                    due = '7_DAYS'

        # If 7_DAYS has been completed or expired, check subsequent milestones
        if due is None:
            # Find reference T1 date
            t1_completed_at = self.posttest_completed_at
            if not t1_completed_at:
                t1_rs = ResponseSet.objects.filter(user=self, status='COMPLETED', milestone='7_DAYS').first()
                if t1_rs:
                    t1_completed_at = t1_rs.completed_at
            
            if t1_completed_at:
                ref_date = t1_completed_at
            else:
                ref_date = self.onboarding_completed_at + timezone.timedelta(days=7)

            # 1.5. 1_MONTH (T-First-Month follow-up)
            if '1_MONTH' not in completed_milestones:
                due_date = ref_date + timezone.timedelta(days=23)  # 30 days total since onboarding
                if now >= due_date:
                    if now - due_date >= timezone.timedelta(days=14):
                        # 1_MONTH has expired.
                        pass
                    else:
                        due = '1_MONTH'

            # 2. 3_MONTHS (T2 follow-up)
            if due is None and '3_MONTHS' not in completed_milestones:
                due_date = ref_date + timezone.timedelta(days=90)
                if now >= due_date:
                    if now - due_date >= timezone.timedelta(days=14):
                        # 3_MONTHS has expired.
                        pass
                    else:
                        due = '3_MONTHS'

            # 3. 6_MONTHS (T3 follow-up)
            if due is None and '6_MONTHS' not in completed_milestones:
                due_date = ref_date + timezone.timedelta(days=180)
                if now >= due_date:
                    if now - due_date >= timezone.timedelta(days=14):
                        # 6_MONTHS has expired.
                        pass
                    else:
                        due = '6_MONTHS'

            # 4. 1_YEAR (T4 follow-up)
            if due is None and '1_YEAR' not in completed_milestones:
                due_date = ref_date + timezone.timedelta(days=365)
                if now >= due_date:
                    if now - due_date >= timezone.timedelta(days=14):
                        # 1_YEAR has expired.
                        pass
                    else:
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

        effective_day = min(current_day, 7)
        wave = self.current_activity_wave
        if not wave:
            return 0

        from activities.models import Submission
        submissions_count = Submission.objects.filter(
            user=self, activity_wave=wave
        ).values('experiment_day').distinct().count()
        
        # Avoid division by zero
        rate = int((submissions_count / effective_day) * 100) if effective_day > 0 else 0
        final_rate = min(rate, 100)
        
        # Cache for 5 minutes
        cache.set(cache_key, final_rate, timeout=300)
        
        return final_rate

    @property
    def has_consecutive_misses(self):
        """
        Returns True if the user has missed submitting daily activities on 2 consecutive days
        during their active week (Days 1 to 7) and has not yet gotten back on track.
        """
        current_day = self.current_experiment_day
        wave = self.current_activity_wave
        if not current_day or not wave or not self.onboarding_completed_at:
            return False

        from activities.models import Submission
        submitted_days = set(
            Submission.objects.filter(user=self, activity_wave=wave, experiment_day__lte=7)
            .values_list('experiment_day', flat=True)
        )

        # If they already submitted today's activity, they are back on track today.
        if current_day in submitted_days:
            return False

        # Scan backwards from yesterday (current_day - 1) to determine the most recent status.
        # If we hit two consecutive missed days before hitting any completed days, they are flagged.
        # If we hit a completed day first, then they got back on track and are not flagged.
        consecutive_miss_count = 0
        for day in range(current_day - 1, 0, -1):
            if day > 7:
                continue
            if day not in submitted_days:
                consecutive_miss_count += 1
                if consecutive_miss_count >= 2:
                    return True
            else:
                # Met a submitted day, the streak of misses is broken
                break
        return False

    @property
    def consecutive_misses_message(self):
        if self.has_consecutive_misses:
            return "We noticed you missed your reflection for a couple of days. Research shows consistency is key to benefit from the intervention. Let's get back on track today!"
        return ""

    @property
    def has_two_consecutive_missed_waves(self):
        """
        Returns True if the last two milestone waves that should have been completed were missed
        (overdue by >= 14 days and no completed response set exists).
        """
        from questionnaires.models import ResponseSet
        completed_milestones = set(
            ResponseSet.objects.filter(
                user=self,
                status='COMPLETED',
                milestone__isnull=False,
                questionnaire__assessment_type='PSYCHOMETRIC'
            )
            .values_list('milestone', flat=True)
        )
        if self.has_completed_posttest:
            completed_milestones.add('7_DAYS')

        if not self.onboarding_completed_at:
            return False

        now = timezone.now()
        
        # Calculate ref_date
        t1_completed_at = self.posttest_completed_at
        if not t1_completed_at:
            t1_rs = ResponseSet.objects.filter(user=self, status='COMPLETED', milestone='7_DAYS').first()
            if t1_rs:
                t1_completed_at = t1_rs.completed_at
        if t1_completed_at:
            ref_date = t1_completed_at
        else:
            ref_date = self.onboarding_completed_at + timezone.timedelta(days=7)

        # Waves and their due dates
        waves = [
            ('7_DAYS', self.onboarding_completed_at + timezone.timedelta(days=7)),
            ('1_MONTH', ref_date + timezone.timedelta(days=23)),
            ('3_MONTHS', ref_date + timezone.timedelta(days=90)),
            ('6_MONTHS', ref_date + timezone.timedelta(days=180)),
            ('1_YEAR', ref_date + timezone.timedelta(days=365)),
        ]

        # Check waves that are past the 14-day expiry window
        missed_flags = []
        for milestone, due_date in waves:
            expiry_date = due_date + timezone.timedelta(days=14)
            if now >= expiry_date:
                # Wave has expired. Was it completed?
                is_completed = milestone in completed_milestones
                missed_flags.append(not is_completed)
            else:
                # This and subsequent waves are not yet past expiry
                break

        # Check if last two in the list of past/expired waves are both True (missed)
        if len(missed_flags) >= 2:
            return missed_flags[-1] and missed_flags[-2]
        return False


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
