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
        group=test_group, has_completed_baseline=True
    )
    # User 2: Has completed baseline, ALREADY submitted today
    u2 = User.objects.create_user(
        username="p2", email="p2@test.com", password="pwd", 
        group=test_group, has_completed_baseline=True
    )
    # User 3: Has NOT completed baseline (should not be reminded of daily tasks)
    u3 = User.objects.create_user(
        username="p3", email="p3@test.com", password="pwd", 
        group=test_group, has_completed_baseline=False
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
