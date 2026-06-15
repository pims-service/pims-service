import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def send_notification(self, notification_id):
    """Send a pending notification asynchronously and mark it as sent or failed."""
    from notifications.models import Notification

    try:
        notification = Notification.objects.get(pk=notification_id)
        logger.info(
            "Sending %s notification (id=%s) to user %s",
            notification.n_type,
            notification_id,
            notification.user_id,
        )
        
        # Send actual email if n_type is 'email'
        if notification.n_type == 'email':
            from django.core.mail import EmailMultiAlternatives
            from django.conf import settings
            
            user = notification.user
            if not user.is_active:
                logger.error("User %s is inactive, skipping email send.", user.username)
                notification.status = 'failed'
                notification.save(update_fields=['status'])
                return {'status': 'failed', 'reason': 'inactive_user', 'notification_id': notification_id}
                
            if not user.email:
                logger.error("User %s does not have an email address configured, skipping email send.", user.username)
                notification.status = 'failed'
                notification.save(update_fields=['status'])
                return {'status': 'failed', 'reason': 'missing_email', 'notification_id': notification_id}
                
            name = user.display_name
            
            msg_lower = notification.message.lower()
            if 'reflection' in msg_lower:
                from emails.builder import (
                    build_daily_nudge_email,
                    build_evening_reminder_email,
                    build_consecutive_misses_email,
                    get_first_name,
                )
                from emails.booster_schedule import get_active_writing_day
                from emails.tasks import _send_participant_email

                first_name = get_first_name(user)
                writing_day = get_active_writing_day(user)
                if writing_day:
                    phase = writing_day.phase_number
                    day = writing_day.day_in_phase
                else:
                    phase = 1
                    day = 1

                if 'missed' in msg_lower:
                    email_content = build_consecutive_misses_email(first_name, phase=phase, day_in_phase=day)
                elif 'evening' in msg_lower:
                    email_content = build_evening_reminder_email(first_name, phase=phase, day_in_phase=day)
                else:
                    email_content = build_daily_nudge_email(first_name, phase=phase, day_in_phase=day)

                _send_participant_email(email_content, user.email)
                logger.info("Successfully sent daily activity nudge email to %s", user.email)
            else:
                if 'overdue' in msg_lower:
                    subject = "PIMS Assessment Overdue Reminder"
                    title = "Assessment Overdue Reminder"
                else:
                    subject = "PIMS Assessment Due Reminder"
                    title = "Assessment Due Reminder"
                button_text = "Go to Dashboard"
                dashboard_url = "https://psycheversity.com/dashboard"

                text_content = f"Hi {name},\n\n{notification.message}\n\nPlease visit your dashboard: {dashboard_url}"

                html_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e4e4e7; border-radius: 8px;">
                    <h2 style="color: #18181b; margin-top: 0;">{title}</h2>
                    <p style="font-size: 16px; color: #18181b;">Hi {name},</p>
                    <p style="color: #3f3f46; font-size: 16px; line-height: 1.5;">{notification.message}</p>
                    <div style="margin: 25px 0;">
                        <a href="{dashboard_url}" style="background-color: #18181b; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">{button_text}</a>
                    </div>
                    <hr style="border: 0; border-top: 1px solid #e4e4e7; margin: 20px 0;">
                    <p style="color: #71717a; font-size: 12px; margin-bottom: 0;">This is an automated message from the Psychological Intervention Platform. Please do not reply directly to this email.</p>
                </div>
                """

                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send(fail_silently=False)
                logger.info("Successfully sent email notification to %s", user.email)
            
        notification.status = 'sent'
        notification.save(update_fields=['status'])
        return {'status': 'sent', 'notification_id': notification_id}
    except Notification.DoesNotExist:
        logger.error("Notification id=%s not found", notification_id)
        raise
    except Exception as exc:
        logger.error("Failed to send notification id=%s: %s", notification_id, exc)
        Notification.objects.filter(pk=notification_id).update(status='failed')
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task
def check_and_send_daily_reminders(reminder_type='morning'):
    """
    Identifies participants who haven't submitted their daily activity
    and sends them a nudge (email/whatsapp).
    """
    from django.contrib.auth import get_user_model
    from activities.models import Submission
    from notifications.models import Notification
    from django.utils import timezone
    from datetime import datetime

    User = get_user_model()
    
    # Define today's range
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Find active participants who haven't finished baseline yet OR have finished it but haven't submitted today
    # (Actually, users only start daily tasks AFTER baseline)
    participants = User.objects.filter(has_completed_sociodemographic=True, is_active=True)
    
    reminded_count = 0
    for user in participants:
        # Check if the user has an active daily reflection block today
        if not user.current_experiment_day:
            continue

        # Check if user submitted today
        has_submitted = Submission.objects.filter(
            user=user,
            submission_date__gte=today_start
        ).exists()
        
        if not has_submitted:
            if user.has_consecutive_misses:
                msg = "We noticed you missed your reflection for a couple of days. Research shows consistency is key to benefit from the intervention. Let's get back on track today!"
            else:
                msg = "Good morning! Don't forget to complete your daily reflection today."
                if reminder_type == 'evening':
                    msg = "Good evening! You haven't completed your daily reflection yet. There's still time!"
            
            # Create email notification for daily reflection reminder
            n_type = 'email'
            n = Notification.objects.create(
                user=user,
                n_type=n_type,
                message=msg,
                scheduled_time=timezone.now(),
                status='pending'
            )
            send_notification.delay(n.id)
            reminded_count += 1
            
    return f"Sent {reminded_count} {reminder_type} reminders."


@shared_task
def send_longitudinal_milestone_reminders():
    """
    Identifies participants who are due for longitudinal milestones
    and dispatches a notification/reminder to them.
    """
    from django.contrib.auth import get_user_model
    from notifications.models import Notification
    from django.core.cache import cache
    from django.utils import timezone

    User = get_user_model()
    # Query chunking for KVM2 memory optimization
    active_participants = User.objects.filter(
        is_active=True, 
        has_completed_sociodemographic=True
    ).iterator(chunk_size=1000)

    reminded_count = 0
    now = timezone.now()

    for user in active_participants:
        due_milestone = user.get_due_milestone
        
        # We only remind for longitudinal post-baseline milestones
        if due_milestone not in ['7_DAYS', '1_MONTH', '3_MONTHS', '6_MONTHS', '1_YEAR']:
            continue

        # Prevent double-reminding for the same milestone (cached for 15 days, since milestone window is 14 days)
        reminder_sent_key = f"user_{user.user_id}_reminded_initial_{due_milestone}"
        if cache.get(reminder_sent_key):
            continue

        # Map milestone to custom reminder message
        milestone_labels = {
            '7_DAYS': '7-day post-test',
            '1_MONTH': '1-month follow-up',
            '3_MONTHS': '3-month follow-up',
            '6_MONTHS': '6-month follow-up',
            '1_YEAR': '1-year follow-up',
        }
        label = milestone_labels.get(due_milestone, 'follow-up')
        
        if user.has_two_consecutive_missed_waves:
            msg = f"PIMS Final Re-engagement: We noticed you missed your previous follow-ups. This is our final attempt to re-engage you for the {label} assessment. Please complete it to stay active in the study."
        else:
            msg = f"Hello! Your {label} assessment is now due. Please complete it today!"

        n = Notification.objects.create(
            user=user,
            n_type='email',
            message=msg,
            scheduled_time=now,
            status='pending'
        )
        
        send_notification.delay(n.id)

        # Cache the sent status for 15 days to prevent duplicate initial sending across the due window
        cache.set(reminder_sent_key, True, timeout=15 * 86400)

        reminded_count += 1

    return f"Sent {reminded_count} longitudinal milestone reminders."


@shared_task
def run_tier3_daily_evaluation():
    """
    Identifies participants who reached Day 8+ and completed <= 2 submissions,
    then creates a support ticket representing a required clinical call.
    """
    from django.contrib.auth import get_user_model
    from activities.models import Submission
    from support.models import SupportTicket
    from django.utils import timezone
    
    User = get_user_model()
    # Only active participants who completed onboarding
    users = User.objects.filter(is_active=True, has_completed_sociodemographic=True)
    
    from activities.timeline import get_waves_for_tier3_evaluation, WAVE_LABELS

    tickets_created = 0
    for user in users:
        for wave in get_waves_for_tier3_evaluation(user):
            sub_count = Submission.objects.filter(
                user=user, activity_wave=wave, experiment_day__lte=7
            ).values('experiment_day').distinct().count()
            if sub_count > 2:
                continue

            subject = f"Call Protocol: High Daily Activity Miss Rate ({wave})"
            exists = SupportTicket.objects.filter(user=user, subject=subject).exists()
            if exists:
                continue

            wave_label = WAVE_LABELS.get(wave, wave)
            SupportTicket.objects.create(
                user=user,
                subject=subject,
                message=(
                    f"Participant {user.full_name or user.username} completed the {wave_label} "
                    f"activity block with only {sub_count} daily activities out of 7. "
                    "Please place a call within 72 hours using the supportive script."
                ),
                status='Open',
            )
            tickets_created += 1
    return f"Tier 3 evaluation completed. Created {tickets_created} tickets."


@shared_task
def run_assessment_graduated_reminders():
    """
    Checks active participants with currently due milestones and sends graduated reminders
    based on how many days the milestone is overdue.
    """
    from django.contrib.auth import get_user_model
    from notifications.models import Notification
    from support.models import SupportTicket
    from django.utils import timezone
    from django.core.cache import cache
    
    User = get_user_model()
    users = User.objects.filter(is_active=True, has_completed_sociodemographic=True)
    
    now = timezone.now()
    today_date = now.date()
    reminders_sent = 0
    tickets_created = 0
    
    for user in users:
        due_milestone = user.get_due_milestone
        if not due_milestone or due_milestone == 'SIGNUP':
            continue

        if user.has_two_consecutive_missed_waves:
            # Tier 5: Only one final re-engagement attempt is sent when the milestone becomes due (initial reminder).
            # No further notifications, messages or support calls are generated for this wave if they miss it.
            continue
            
        # Get ref_date (T1 completion date)
        from questionnaires.models import ResponseSet
        t1_completed_at = user.posttest_completed_at
        if not t1_completed_at:
            t1_rs = ResponseSet.objects.filter(user=user, status='COMPLETED', milestone='7_DAYS').first()
            if t1_rs:
                t1_completed_at = t1_rs.completed_at
                
        if t1_completed_at:
            ref_date = t1_completed_at
        else:
            ref_date = user.onboarding_completed_at + timezone.timedelta(days=7)
            
        if due_milestone == '7_DAYS':
            due_date = user.onboarding_completed_at + timezone.timedelta(days=7)
        elif due_milestone == '1_MONTH':
            due_date = ref_date + timezone.timedelta(days=23)
        elif due_milestone == '3_MONTHS':
            due_date = ref_date + timezone.timedelta(days=90)
        elif due_milestone == '6_MONTHS':
            due_date = ref_date + timezone.timedelta(days=180)
        elif due_milestone == '1_YEAR':
            due_date = ref_date + timezone.timedelta(days=365)
        else:
            continue
            
        # Compute overdue days (since the start of the due date, day-based)
        today_date = timezone.localdate()
        due_date_local = timezone.localtime(due_date).date()
        overdue_days = (today_date - due_date_local).days
        
        if overdue_days <= 0:
            continue
            
        n_type = None
        message = None
        
        milestone_labels = {
            '7_DAYS': '7-day post-test',
            '1_MONTH': '1-month follow-up',
            '3_MONTHS': '3-month follow-up',
            '6_MONTHS': '6-month follow-up',
            '1_YEAR': '1-year follow-up',
        }
        label = milestone_labels[due_milestone]
        
        if overdue_days == 1:
            n_type = 'email'
            message = f"Reminder: Your {label} assessment is overdue. Please complete it at your earliest convenience."
        elif overdue_days == 3:
            n_type = 'whatsapp'
            message = f"Hello! Your {label} assessment is 3 days overdue. Please click the link on your dashboard to complete it."
        elif overdue_days == 7:
            n_type = 'sms'
            message = f"PIMS Alert: Your {label} assessment is now 7 days overdue. Please complete it soon to continue in the study."
        elif overdue_days >= 10:
            # Create a Call ticket
            exists = SupportTicket.objects.filter(
                user=user,
                subject__icontains=f"Call Protocol: Assessment Overdue ({due_milestone})"
            ).exists()
            if not exists:
                SupportTicket.objects.create(
                    user=user,
                    subject=f"Call Protocol: Assessment Overdue ({due_milestone}) - Tier 4",
                    message=f"Participant {user.full_name or user.username} has not completed their {label} assessment, which is now 10 days overdue. Please call within 72 hours using the supportive script.",
                    status='Open'
                )
                tickets_created += 1
                
        if n_type and message:
            sent_key = f"user_{user.user_id}_overdue_reminded_{due_milestone}_{overdue_days}_{today_date}"
            if not cache.get(sent_key):
                n = Notification.objects.create(
                    user=user,
                    n_type=n_type,
                    message=message,
                    scheduled_time=now,
                    status='pending'
                )
                send_notification.delay(n.id)
                cache.set(sent_key, True, timeout=86400)
                reminders_sent += 1
                
    return f"Graduated reminders sent: {reminders_sent}. Support call tickets created: {tickets_created}."
