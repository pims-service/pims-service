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

    subject = "Your Email Verification Code"
    text_content = f"Hello, your verification code is {otp}."
    html_content = f"<h3>Welcome!</h3><p>Your email verification code is: <strong>{otp}</strong></p><p>This code will expire in 10 minutes.</p>"

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
