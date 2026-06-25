import logging

from celery import shared_task
from celery.exceptions import Retry
from django.conf import settings
from django.contrib.auth import get_user_model

from .builder import (
    build_socio_disqualification_email,
    build_support_email,
    build_welcome_email,
    get_first_name,
)

logger = logging.getLogger(__name__)
User = get_user_model()


def _send_participant_email(
    email_content: dict[str, str],
    recipient: str,
    *,
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> None:
    from django.core.mail import EmailMultiAlternatives

    msg = EmailMultiAlternatives(
        subject=email_content['subject'],
        body=email_content['text_content'],
        from_email=settings.PARTICIPANT_EMAIL_FROM,
        to=[recipient],
        reply_to=[settings.PARTICIPANT_EMAIL_REPLY_TO],
    )
    msg.attach_alternative(email_content['html_content'], 'text/html')
    for filename, content, mimetype in attachments or []:
        msg.attach(filename, content, mimetype)
    msg.send(fail_silently=False)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_welcome_email_task(self, user_id: int):
    """Send the E1 bilingual welcome email after successful onboarding (Day 0)."""
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error('Welcome email skipped: user %s not found', user_id)
        return {'status': 'skipped', 'reason': 'user_not_found'}

    if not user.email:
        logger.error('Welcome email skipped: user %s has no email', user.username)
        return {'status': 'skipped', 'reason': 'missing_email'}

    if user.is_disqualified:
        logger.info('Welcome email skipped: user %s is disqualified', user.username)
        return {'status': 'skipped', 'reason': 'disqualified'}

    if not user.onboarding_completed_at:
        logger.info('Welcome email skipped: user %s has not completed onboarding', user.username)
        return {'status': 'skipped', 'reason': 'onboarding_incomplete'}

    first_name = get_first_name(user)
    email_content = build_welcome_email(first_name)

    try:
        _send_participant_email(email_content, user.email)
        logger.info('Successfully sent welcome email to %s (%s)', user.username, user.email)
        return {'status': 'sent', 'recipient': user.email}
    except Exception as exc:
        logger.error('Error sending welcome email to %s: %s', user.email, exc)
        if isinstance(exc, Retry):
            raise
        raise self.retry(exc=exc) from exc


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_support_email_task(self, user_id: int):
    """Send bilingual support resources when suicide-risk protocol is triggered."""
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error('Support email skipped: user %s not found', user_id)
        return {'status': 'skipped', 'reason': 'user_not_found'}

    if not user.email:
        logger.error('Support email skipped: user %s has no email', user.username)
        return {'status': 'skipped', 'reason': 'missing_email'}

    if user.is_disqualified:
        logger.info('Support email skipped: user %s is disqualified', user.username)
        return {'status': 'skipped', 'reason': 'disqualified'}

    first_name = get_first_name(user)
    email_content = build_support_email(first_name)

    try:
        _send_participant_email(email_content, user.email)
        logger.info('Successfully sent support email to %s (%s)', user.username, user.email)
        return {'status': 'sent', 'recipient': user.email}
    except Exception as exc:
        logger.error('Error sending support email to %s: %s', user.email, exc)
        if isinstance(exc, Retry):
            raise
        raise self.retry(exc=exc) from exc


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_socio_disqualification_email_task(self, user_id: int):
    """Send bilingual eligibility disqualification email after sociodemographic screen-out."""
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error('Socio disqualification email skipped: user %s not found', user_id)
        return {'status': 'skipped', 'reason': 'user_not_found'}

    if not user.email:
        logger.error('Socio disqualification email skipped: user %s has no email', user.username)
        return {'status': 'skipped', 'reason': 'missing_email'}

    if not user.is_disqualified:
        logger.info('Socio disqualification email skipped: user %s is not disqualified', user.username)
        return {'status': 'skipped', 'reason': 'not_disqualified'}

    first_name = get_first_name(user)
    email_content = build_socio_disqualification_email(first_name)

    try:
        _send_participant_email(email_content, user.email)
        logger.info(
            'Successfully sent socio disqualification email to %s (%s)',
            user.username,
            user.email,
        )
        return {'status': 'sent', 'recipient': user.email}
    except Exception as exc:
        logger.error('Error sending socio disqualification email to %s: %s', user.email, exc)
        if isinstance(exc, Retry):
            raise
        raise self.retry(exc=exc) from exc


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_ticket_created_participant_email_task(self, ticket_id: int):
    from support.models import SupportTicket
    from .builder import build_ticket_created_participant_email, get_first_name

    try:
        ticket = SupportTicket.objects.select_related('user').get(pk=ticket_id)
    except SupportTicket.DoesNotExist:
        logger.error('Ticket created participant email skipped: ticket %s not found', ticket_id)
        return {'status': 'skipped', 'reason': 'ticket_not_found'}

    user = ticket.user
    if not user.email:
        logger.error('Ticket created participant email skipped: user %s has no email', user.username)
        return {'status': 'skipped', 'reason': 'missing_email'}

    first_name = get_first_name(user)
    email_content = build_ticket_created_participant_email(
        first_name=first_name,
        ticket_number=ticket.ticket_number,
        subject=ticket.subject,
    )

    try:
        _send_participant_email(email_content, user.email)
        logger.info('Successfully sent ticket creation email to participant %s (%s) for ticket %s', user.username, user.email, ticket.ticket_number)
        return {'status': 'sent', 'recipient': user.email, 'ticket_number': ticket.ticket_number}
    except Exception as exc:
        logger.error('Error sending ticket creation email to participant %s: %s', user.email, exc)
        if isinstance(exc, Retry):
            raise
        raise self.retry(exc=exc) from exc


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_ticket_created_admin_email_task(self, ticket_id: int):
    from support.models import SupportTicket
    from .builder import build_ticket_created_admin_email
    from django.core.mail import EmailMultiAlternatives

    try:
        ticket = SupportTicket.objects.select_related('user').get(pk=ticket_id)
    except SupportTicket.DoesNotExist:
        logger.error('Ticket created admin email skipped: ticket %s not found', ticket_id)
        return {'status': 'skipped', 'reason': 'ticket_not_found'}

    user = ticket.user
    email_content = build_ticket_created_admin_email(
        ticket_number=ticket.ticket_number,
        user_name=user.full_name or user.username,
        user_email=user.email or "no-email@psycheversity.com",
        subject=ticket.subject,
        message=ticket.message,
    )

    recipient = settings.SUPPORT_ADMIN_EMAIL

    msg = EmailMultiAlternatives(
        subject=email_content['subject'],
        body=email_content['text_content'],
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    msg.attach_alternative(email_content['html_content'], 'text/html')

    try:
        msg.send(fail_silently=False)
        logger.info('Successfully sent ticket creation email to admin (%s) for ticket %s', recipient, ticket.ticket_number)
        return {'status': 'sent', 'recipient': recipient, 'ticket_number': ticket.ticket_number}
    except Exception as exc:
        logger.error('Error sending ticket creation email to admin %s: %s', recipient, exc)
        if isinstance(exc, Retry):
            raise
        raise self.retry(exc=exc) from exc


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_ticket_updated_participant_email_task(self, ticket_id: int):
    from support.models import SupportTicket
    from .builder import build_ticket_updated_participant_email, get_first_name

    try:
        ticket = SupportTicket.objects.select_related('user').get(pk=ticket_id)
    except SupportTicket.DoesNotExist:
        logger.error('Ticket updated participant email skipped: ticket %s not found', ticket_id)
        return {'status': 'skipped', 'reason': 'ticket_not_found'}

    user = ticket.user
    if not user.email:
        logger.error('Ticket updated participant email skipped: user %s has no email', user.username)
        return {'status': 'skipped', 'reason': 'missing_email'}

    first_name = get_first_name(user)
    email_content = build_ticket_updated_participant_email(
        first_name=first_name,
        ticket_number=ticket.ticket_number,
        status=ticket.status,
        admin_reply=ticket.admin_reply,
    )

    try:
        _send_participant_email(email_content, user.email)
        logger.info('Successfully sent ticket update email to participant %s (%s) for ticket %s', user.username, user.email, ticket.ticket_number)
        return {'status': 'sent', 'recipient': user.email, 'ticket_number': ticket.ticket_number}
    except Exception as exc:
        logger.error('Error sending ticket update email to participant %s: %s', user.email, exc)
        if isinstance(exc, Retry):
            raise
        raise self.retry(exc=exc) from exc



# Ensure Celery autodiscovery registers these tasks
from .booster_tasks import (
    send_booster_daily_nudges,
    send_booster_phase_invites,
    send_daily_nudge_email_task,
    send_phase_invite_email_task,
    send_phase_complete_email_task,
)

