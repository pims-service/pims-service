import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from notifications.tasks import check_and_send_daily_reminders
from notifications.models import Notification
from activities.models import Activity, Submission
from users.models import User

@pytest.fixture
def participants(db, test_group):
    # User 1: Has completed baseline, hasn't submitted today
    u1 = User.objects.create_user(
        username="p1", email="p1@test.com", password="pwd", 
        group=test_group, has_completed_sociodemographic=True
    )
    # User 2: Has completed baseline, ALREADY submitted today
    u2 = User.objects.create_user(
        username="p2", email="p2@test.com", password="pwd", 
        group=test_group, has_completed_sociodemographic=True
    )
    # User 3: Has NOT completed baseline (should not be reminded of daily tasks)
    u3 = User.objects.create_user(
        username="p3", email="p3@test.com", password="pwd", 
        group=test_group, has_completed_sociodemographic=False
    )
    return u1, u2, u3

@pytest.fixture
def today_activity(db, test_group, test_phase):
    return Activity.objects.create(
        title="Today Task", description="Desc", 
        assigned_phase=test_phase, group=test_group, activity_type="paragraph"
    )

@pytest.mark.django_db
class TestDailyReminders:
    """
    Business logic tests for the automated daily nudge system.
    Ensures notifications are only sent to targeted participants.
    """

    @patch('notifications.tasks.send_notification.delay')
    def test_morning_reminder_targets_only_missing_submissions(self, mock_delay, participants, today_activity):
        u1, u2, u3 = participants
        
        # Mark User 2 as having submitted today
        Submission.objects.create(user=u2, activity=today_activity, content="Done")
        
        # Run morning reminder
        result = check_and_send_daily_reminders(reminder_type='morning')
        
        # Assertions
        assert "Sent 1 morning reminders" in result
        
        # Verify User 1 got a notification, but User 2 and 3 did not
        assert Notification.objects.filter(user=u1, message__icontains="morning").exists()
        assert not Notification.objects.filter(user=u2).exists()
        assert not Notification.objects.filter(user=u3).exists()
        
        # Verify Celery delay was called exactly once
        assert mock_delay.call_count == 1

    @patch('notifications.tasks.send_notification.delay')
    def test_evening_reminder_message_content(self, mock_delay, participants, today_activity):
        u1, u2, u3 = participants
        
        # Run evening reminder
        result = check_and_send_daily_reminders(reminder_type='evening')
        
        assert "Sent 2 evening reminders" in result # User 1 and User 2 both haven't submitted
        
        # Verify evening specific message
        notification = Notification.objects.filter(user=u1).first()
        assert "Good evening" in notification.message
        assert "still time" in notification.message


@pytest.mark.django_db
class TestLongitudinalReminders:
    """
    Test suite for send_longitudinal_milestone_reminders task.
    """

    @pytest.fixture(autouse=True)
    def clear_redis_cache(self):
        from django.core.cache import cache
        cache.clear()
        yield
        cache.clear()

    @patch('notifications.tasks.send_notification.delay')
    def test_milestone_reminders_targeting(self, mock_delay, test_group):
        from notifications.tasks import send_longitudinal_milestone_reminders
        from datetime import timedelta
        from django.utils import timezone
        from questionnaires.models import Questionnaire, ResponseSet

        # 1. User who completed baseline exactly 7 days ago (7_DAYS is due)
        u1 = User.objects.create_user(
            username="due_7_days", email="u1@test.com", password="pwd",
            group=test_group, has_completed_sociodemographic=True,
            onboarding_completed_at=timezone.now() - timedelta(days=7)
        )

        # 2. User who completed baseline 3 days ago (not due for anything yet)
        u2 = User.objects.create_user(
            username="not_due", email="u2@test.com", password="pwd",
            group=test_group, has_completed_sociodemographic=True,
            onboarding_completed_at=timezone.now() - timedelta(days=3)
        )

        # 3. User who completed baseline 90 days ago but already completed the 3_MONTHS milestone (and 7_DAYS milestone)
        u3 = User.objects.create_user(
            username="already_done_3m", email="u3@test.com", password="pwd",
            group=test_group, has_completed_sociodemographic=True,
            onboarding_completed_at=timezone.now() - timedelta(days=90)
        )
        q = Questionnaire.objects.create(title="Battery", assessment_type="PSYCHOMETRIC")
        ResponseSet.objects.create(user=u3, questionnaire=q, status='COMPLETED', milestone='7_DAYS')
        ResponseSet.objects.create(user=u3, questionnaire=q, status='COMPLETED', milestone='3_MONTHS')

        # Run task
        result = send_longitudinal_milestone_reminders()

        # Assertions
        assert "Sent 1 longitudinal milestone reminders" in result
        
        # Verify u1 received the notification
        assert Notification.objects.filter(user=u1, message__icontains="7-day").exists()
        # Verify u2 and u3 did not
        assert not Notification.objects.filter(user=u2).exists()
        assert not Notification.objects.filter(user=u3).exists()

        # Celery task should be called exactly once (for u1)
        assert mock_delay.call_count == 1

        # 4. Running the task again on the same day should send 0 reminders (cached key prevents duplication)
        mock_delay.reset_mock()
        result_retry = send_longitudinal_milestone_reminders()
        assert "Sent 0 longitudinal milestone reminders" in result_retry
        assert mock_delay.call_count == 0


@pytest.mark.django_db
class TestMissedDayProtocol:
    """
    Test suite verifying the Missed Day Protocol (Tiers 1-5).
    """

    @pytest.fixture(autouse=True)
    def clear_redis_cache(self):
        from django.core.cache import cache
        cache.clear()
        yield
        cache.clear()

    def test_consecutive_missed_days(self, test_group):
        from datetime import timedelta
        # Setup user in experiment at Day 3 (onboarding completed 2 days ago)
        user = User.objects.create_user(
            username="consec", email="consec@test.com", password="pwd",
            group=test_group, has_completed_sociodemographic=True,
            onboarding_completed_at=timezone.now() - timedelta(days=2)
        )
        # Verify user is on Day 3
        assert user.current_experiment_day == 3

        # Since Day 1 and Day 2 have no submissions, user has consecutive misses
        assert user.has_consecutive_misses is True
        assert "consistency is key" in user.consecutive_misses_message

        # Add a submission on Day 1
        from activities.models import Activity
        from phases.models import Phase
        phase = Phase.objects.create(phase_number=1, name="Phase 1", start_date=timezone.now().date() - timedelta(days=10), end_date=timezone.now().date() + timedelta(days=10))
        act = Activity.objects.create(title="Reflection", assigned_phase=phase, day_number=1)
        Submission.objects.create(user=user, activity=act, experiment_day=1)

        # Clear cache since model save signals reset user calculations
        from django.core.cache import cache
        cache.clear()

        # Day 2 is still missed, but Day 1 is submitted, so no consecutive misses
        assert user.has_consecutive_misses is False
        assert user.consecutive_misses_message == ""

        # Remove submission on Day 1 to flag them again
        Submission.objects.filter(user=user, experiment_day=1).delete()
        cache.clear()
        assert user.has_consecutive_misses is True

        # Submit today's activity (Day 3)
        act3 = Activity.objects.create(title="Reflection 3", assigned_phase=phase, day_number=3)
        Submission.objects.create(user=user, activity=act3, experiment_day=3)
        cache.clear()

        # Flag should clear immediately
        assert user.has_consecutive_misses is False
        assert user.consecutive_misses_message == ""

    def test_tier3_missed_day_protocol_ticket_creation(self, test_group):
        from datetime import timedelta
        from notifications.tasks import run_tier3_daily_evaluation
        from support.models import SupportTicket

        # Setup user at Day 8 (onboarding completed 7 days ago)
        user = User.objects.create_user(
            username="t3_user", email="t3@test.com", password="pwd",
            group=test_group, has_completed_sociodemographic=True,
            onboarding_completed_at=timezone.now() - timedelta(days=7)
        )
        assert user.current_experiment_day is None

        # With 0 submissions (<= 2), the user should trigger Tier 3 Call Protocol
        result = run_tier3_daily_evaluation()
        assert "Created 1 tickets" in result

        ticket = SupportTicket.objects.filter(user=user).first()
        assert ticket is not None
        assert "Call Protocol" in ticket.subject
        assert "(PRE_T1)" in ticket.subject
        assert ticket.status == 'Open'

    def test_tier4_assessment_milestone_expiration(self, test_group):
        from datetime import timedelta

        # Setup user with onboarding completed 22 days ago
        user = User.objects.create_user(
            username="t4_expired", email="t4@test.com", password="pwd",
            group=test_group, has_completed_sociodemographic=True,
            onboarding_completed_at=timezone.now() - timedelta(days=22)
        )
        # The 7_DAYS milestone became due at onboarding + 7 days (15 days ago).
        # Since it is overdue by 15 days (>= 14 days), it must expire, so get_due_milestone
        # should skip 7_DAYS and return None (since 3_MONTHS is not due yet)
        assert user.get_due_milestone is None

    @patch('notifications.tasks.send_notification.delay')
    def test_tier4_graduated_reminders(self, mock_delay, test_group):
        from datetime import timedelta
        from notifications.tasks import run_assessment_graduated_reminders
        from support.models import SupportTicket

        # 1. Overdue by 1 day -> Email
        u1 = User.objects.create_user(
            username="u1_od", email="u1@test.com", password="pwd",
            group=test_group, has_completed_sociodemographic=True,
            onboarding_completed_at=timezone.now() - timedelta(days=8)
        )
        # 2. Overdue by 3 days -> WhatsApp
        u2 = User.objects.create_user(
            username="u2_od", email="u2@test.com", password="pwd",
            group=test_group, has_completed_sociodemographic=True,
            onboarding_completed_at=timezone.now() - timedelta(days=10)
        )
        # 3. Overdue by 7 days -> SMS
        u3 = User.objects.create_user(
            username="u3_od", email="u3@test.com", password="pwd",
            group=test_group, has_completed_sociodemographic=True,
            onboarding_completed_at=timezone.now() - timedelta(days=14)
        )
        # 4. Overdue by 10 days -> Support call ticket
        u4 = User.objects.create_user(
            username="u4_od", email="u4@test.com", password="pwd",
            group=test_group, has_completed_sociodemographic=True,
            onboarding_completed_at=timezone.now() - timedelta(days=17)
        )

        result = run_assessment_graduated_reminders()
        assert "Graduated reminders sent: 3" in result
        assert "Support call tickets created: 1" in result

        # Verify channels
        assert Notification.objects.filter(user=u1, n_type='email').exists()
        assert Notification.objects.filter(user=u2, n_type='whatsapp').exists()
        assert Notification.objects.filter(user=u3, n_type='sms').exists()
        
        # Verify call ticket
        ticket = SupportTicket.objects.filter(user=u4).first()
        assert ticket is not None
        assert "Call Protocol" in ticket.subject
        assert "Tier 4" in ticket.subject
        assert ticket.status == 'Open'

    @patch('notifications.tasks.send_notification.delay')
    def test_tier5_consecutive_missed_waves(self, mock_delay, test_group):
        from datetime import timedelta
        from notifications.tasks import send_longitudinal_milestone_reminders, run_assessment_graduated_reminders

        # Setup user with onboarding completed 120 days ago (T1 and T2 missed and expired)
        user = User.objects.create_user(
            username="t5_missed", email="t5@test.com", password="pwd",
            group=test_group, has_completed_sociodemographic=True,
            onboarding_completed_at=timezone.now() - timedelta(days=120)
        )
        
        # Verify that the user has missed 2 consecutive waves (T1 and T2 are expired)
        # T1 (7 days after onboarding) expired on day 21. T2 (90 days after onboarding) expired on day 104.
        assert user.has_two_consecutive_missed_waves is True

        # Now set onboarding_completed_at to exactly 187 days ago, so T3 (6_MONTHS / 180 days after T1 due date of 7 days) is due today
        user.onboarding_completed_at = timezone.now() - timedelta(days=187)
        user.save()
        from django.core.cache import cache
        cache.clear()

        # Run reminders - should trigger the final re-engagement message
        send_longitudinal_milestone_reminders()
        
        notification = Notification.objects.filter(user=user).first()
        assert notification is not None
        assert "Final Re-engagement" in notification.message

        # Verify that run_assessment_graduated_reminders does not send any further reminders
        # even when overdue by 8 days (187 + 8 = 195 days since onboarding)
        Notification.objects.all().delete()
        user.onboarding_completed_at = timezone.now() - timedelta(days=195)
        user.save()
        cache.clear()

        result = run_assessment_graduated_reminders()
        assert "Graduated reminders sent: 0" in result
        assert Notification.objects.filter(user=user).count() == 0
