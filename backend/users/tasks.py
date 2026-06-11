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


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_password_reset_email_task(self, email, name, otp):
    """
    Sends the password reset OTP email to the user.
    """
    subject = "PIMS Password Reset Request"
    text_content = f"Hello {name},\n\nWe received a request to reset your password. Your verification code is: {otp}.\n\nThis code will expire in 10 minutes. If you did not request this, please ignore this email."
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e4e4e7; border-radius: 8px;">
        <h2 style="color: #18181b; margin-top: 0;">Password Reset Verification</h2>
        <p style="font-size: 16px; color: #18181b;">Hi {name},</p>
        <p style="color: #3f3f46; font-size: 16px; line-height: 1.5;">We received a request to reset your password. Use the verification code below to proceed:</p>
        <div style="margin: 25px 0; text-align: center;">
            <span style="background-color: #f4f4f5; color: #18181b; font-size: 32px; font-weight: bold; letter-spacing: 4px; padding: 12px 30px; border: 2px solid #e4e4e7; border-radius: 6px; display: inline-block;">{otp}</span>
        </div>
        <p style="color: #ef4444; font-size: 14px;">This code will expire in 10 minutes. For security, please do not share this code with anyone.</p>
        <hr style="border: 0; border-top: 1px solid #e4e4e7; margin: 20px 0;">
        <p style="color: #71717a; font-size: 12px; margin-bottom: 0;">If you did not request a password reset, you can safely ignore this email.</p>
    </div>
    """

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

