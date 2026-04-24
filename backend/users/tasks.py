from celery import shared_task
from django.conf import settings
from mailjet_rest import Client
import logging

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60  # Initial retry after 1 minute
)
def send_otp_email_task(self, email, otp):
    """
    Sends the OTP email to the user using Mailjet API asynchronously with retry logic.
    """
    api_key = settings.MAILJET_API_KEY
    api_secret = settings.MAILJET_SECRET_KEY
    sender_email = settings.MAILJET_SENDER_EMAIL

    if api_key == 'mock_api_key_for_local_dev':
        logger.info(f"[MOCK MAILJET] Would send OTP {otp} to {email}")
        return True

    mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    
    data = {
        'Messages': [
            {
                "From": {
                    "Email": sender_email,
                    "Name": "Psych Experiment Platform"
                },
                "To": [
                    {
                        "Email": email,
                        "Name": "Participant"
                    }
                ],
                "Subject": "Your Email Verification Code",
                "TextPart": f"Hello, your verification code is {otp}.",
                "HTMLPart": f"<h3>Welcome!</h3><p>Your email verification code is: <strong>{otp}</strong></p><p>This code will expire in 10 minutes.</p>"
            }
        ]
    }
    
    try:
        result = mailjet.send.create(data=data)
        status_code = result.status_code
        
        if status_code in [200, 201]:
            logger.info(f"Successfully sent OTP to {email}")
            return True

        # Extract error details if available
        try:
            error_details = result.json()
        except Exception:
            error_details = "No detailed error message available."

        if status_code == 429:
            logger.warning(f"Mailjet Rate Limit (429) hit for {email}. Retrying in {self.request.retries + 1} attempt...")
            raise self.retry(exc=Exception("Mailjet Rate Limit"))
        
        if status_code >= 500:
            logger.warning(f"Mailjet Server Error ({status_code}) for {email}. Retrying...")
            raise self.retry(exc=Exception(f"Mailjet Server Error: {status_code}"))

        # Non-retryable errors
        if status_code == 401:
            logger.error(f"MAILJET CRITICAL: Unauthorized (401). Your API Key or Secret is incorrect. {error_details}")
        elif status_code == 403:
            logger.error(f"MAILJET CRITICAL: Forbidden (403). Ensure '{sender_email}' is verified in the Mailjet dashboard. {error_details}")
        else:
            logger.error(f"Mailjet Delivery Failed ({status_code}) for {email}: {error_details}")
        
        return False

    except Exception as e:
        # If it's a Celery retry exception, re-raise it
        from celery.exceptions import Retry
        if isinstance(e, Retry):
            raise e
        
        # For other unexpected exceptions (e.g. timeout, network issue), attempt one retry
        logger.error(f"Unexpected error during OTP delivery to {email}: {str(e)}")
        raise self.retry(exc=e, countdown=60)
