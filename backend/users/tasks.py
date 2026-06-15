from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
import logging

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60  # Initial retry after 1 minute
)
def send_otp_email_task(self, email, otp):
    """
    Sends the OTP email to the user using Django's configured email backend.
    """
    from emails.builder import build_otp_email

    email_data = build_otp_email(otp)
    subject = email_data['subject']
    text_content = email_data['text_content']
    html_content = email_data['html_content']

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email]
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send(fail_silently=False)
        logger.info(f"Successfully sent OTP to {email}")
        return True
    except Exception as e:
        logger.error(f"Error sending email to {email}: {str(e)}")
        # Check if it's a Celery retry exception, re-raise it
        from celery.exceptions import Retry
        if isinstance(e, Retry):
            raise e
        
        # Attempt one retry
        logger.warning(f"Retrying email delivery to {email}...")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_password_reset_email_task(self, email, name, otp):
    """
    Sends the password reset OTP email to the user.
    """
    from emails.builder import build_password_reset_email

    email_data = build_password_reset_email(name, otp)
    subject = email_data['subject']
    text_content = email_data['text_content']
    html_content = email_data['html_content']

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email]
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send(fail_silently=False)
        logger.info(f"Successfully sent password reset email to {email}")
        return True
    except Exception as e:
        logger.error(f"Error sending password reset email to {email}: {str(e)}")
        from celery.exceptions import Retry
        if isinstance(e, Retry):
            raise e
        logger.warning(f"Retrying password reset email delivery to {email}...")
        raise self.retry(exc=e)


