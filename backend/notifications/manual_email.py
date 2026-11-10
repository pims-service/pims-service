"""
Admin-sent (manual) emails: who may receive them, how they are rendered, and the
unsubscribe link every one of them carries.
"""
import html
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

UNSUBSCRIBE_SALT = 'manual-email-unsubscribe'

SIGN_OFF_EN = 'Psycheversity Research Team. support@psycheversity.com'
SIGN_OFF_UR = 'سائیکیورسٹی ریسرچ ٹیم۔ support@psycheversity.com'

SEGMENT_LABELS = {
    'not_started': 'Not started',
    'stopped': 'Stopped',
    'd7_due': '7-day due',
    'all_eligible': 'All eligible',
    'manual': 'Picked by hand',
}


def eligible_recipients():
    """
    Participants who passed the screener and may receive manual emails:
    never disqualified people, staff/admin accounts or anyone who unsubscribed; signups from
    EMAIL_CONSENT_REQUIRED_FROM onward only with email_consent. Mirrors User.accepts_manual_emails.
    """
    User = get_user_model()
    return (
        User.objects.filter(
            is_staff=False,
            is_superuser=False,
            is_active=True,
            is_disqualified=False,
            has_completed_sociodemographic=True,
            email_unsubscribed_at__isnull=True,
        )
        .exclude(role__name='Admin')
        .exclude(email='')
        .filter(Q(created_at__lt=settings.EMAIL_CONSENT_REQUIRED_FROM) | Q(email_consent=True))
    )


def segment_recipients(segment, user_ids=None):
    """Returns the recipient list (users) for a segment, always within eligible_recipients()."""
    from activities.models import Submission
    from questionnaires.models import ResponseSet

    now = timezone.now()
    qs = eligible_recipients()
    any_submission = Exists(Submission.objects.filter(user=OuterRef('pk')))

    if segment == 'all_eligible':
        pass
    elif segment == 'not_started':
        qs = qs.annotate(has_any=any_submission).filter(has_any=False, created_at__lte=now - timedelta(days=2))
    elif segment == 'stopped':
        recent = Exists(Submission.objects.filter(user=OuterRef('pk'), submission_date__gte=now - timedelta(days=3)))
        day7_done = Exists(ResponseSet.objects.filter(user=OuterRef('pk'), status='COMPLETED', milestone='7_DAYS'))
        qs = (
            qs.annotate(has_any=any_submission, has_recent=recent, has_day7=day7_done)
            .filter(has_any=True, has_recent=False, has_day7=False, has_completed_posttest=False)
        )
    elif segment == 'd7_due':
        return [u for u in qs.filter(has_completed_posttest=False) if u.get_due_milestone == '7_DAYS']
    elif segment == 'manual':
        qs = qs.filter(pk__in=user_ids or [])
    else:
        raise ValueError(f"Unknown segment: {segment}")
    return list(qs.order_by('created_at'))


def make_unsubscribe_token(user):
    return signing.dumps({'u': user.pk}, salt=UNSUBSCRIBE_SALT)


def read_unsubscribe_token(token):
    """Returns the user id, or None for a tampered/invalid token."""
    try:
        return signing.loads(token, salt=UNSUBSCRIBE_SALT).get('u')
    except signing.BadSignature:
        return None


def unsubscribe_url(user):
    base = settings.SITE_BASE_URL.rstrip('/')
    return f"{base}/api/notifications/unsubscribe/{make_unsubscribe_token(user)}/"


def personalise(text, first_name):
    # Plain replace (not str.format) so any other braces in an admin's message are left alone.
    return text.replace('{first_name}', first_name)


def build_manual_email(user, subject, body):
    """Psycheversity-branded email for an admin-written subject/body. Returns subject/text/html."""
    from emails.builder import GOLD, LATIN_FONT_STACK, NAVY, URDU_FONT_STACK, get_email_links, get_first_name
    from emails.content import STANDARD_FOOTER

    first_name = get_first_name(user)
    subject = personalise(subject, first_name)
    body = personalise(body, first_name)
    unsubscribe = unsubscribe_url(user)
    links = get_email_links()

    paragraphs = [p.strip() for p in body.replace('\r\n', '\n').split('\n\n') if p.strip()]
    # dir="auto" lets Urdu paragraphs render right-to-left next to English ones.
    paragraphs_html = ''.join(
        f'<p dir="auto" style="margin: 0 0 14px; font-size: 15px; line-height: 1.8; color: #3f3f46;">'
        f'{html.escape(p).replace(chr(10), "<br>")}</p>'
        for p in paragraphs
    )
    # Psycheversity-only footer: the withdraw and support lines of the standard footer
    # (its third line names the partner institute, which manual emails leave out).
    footer_en = [STANDARD_FOOTER['paragraphs_en'][i].format(**links) for i in (0, 1)] + [SIGN_OFF_EN]
    footer_ur = [STANDARD_FOOTER['paragraphs_ur'][i].format(**links) for i in (0, 1)] + [SIGN_OFF_UR]
    footer_html = (
        '<hr style="border: 0; border-top: 1px solid #e4e4e7; margin: 24px 0;">'
        + ''.join(
            f'<p style="margin: 0 0 10px; font-family: {LATIN_FONT_STACK}; font-size: 12px; line-height: 1.5; color: #71717a;">{p}</p>'
            for p in footer_en
        )
        + f'<div dir="rtl" style="font-family: {URDU_FONT_STACK}; text-align: right; margin-top: 16px;">'
        + ''.join(
            f'<p style="margin: 0 0 10px; font-size: 13px; line-height: 1.8; color: #71717a;">{p}</p>'
            for p in footer_ur
        )
        + '</div>'
    )
    unsubscribe_html = (
        f'<p style="margin: 16px 0 0; font-size: 12px; line-height: 1.6; color: #71717a; text-align: center;">'
        f'Don\'t want these emails? <a href="{unsubscribe}" style="color: {NAVY};">Unsubscribe</a>'
        f' &nbsp;/&nbsp; <span style="font-family: {URDU_FONT_STACK};">یہ ای میلز نہیں چاہتے؟</span> '
        f'<a href="{unsubscribe}" style="color: {NAVY}; font-family: {URDU_FONT_STACK};">ان سبسکرائب کریں</a></p>'
    )
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&display=swap" rel="stylesheet">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f4f4f5;">
        <div style="max-width: 600px; margin: 0 auto; padding: 24px 16px;">
            <div style="background-color: #ffffff; border: 1px solid #e4e4e7; border-radius: 8px; padding: 24px;">
                <h1 dir="auto" style="margin: 0 0 18px; font-family: {LATIN_FONT_STACK}; font-size: 22px; color: {NAVY}; border-bottom: 2px solid {GOLD}; padding-bottom: 10px;">
                    {html.escape(subject)}
                </h1>
                <div style="font-family: {LATIN_FONT_STACK}, {URDU_FONT_STACK}; color: #18181b;">
                    {paragraphs_html}
                    <p style="margin: 18px 0 4px; font-size: 15px; line-height: 1.6;">Warm regards,</p>
                    <p style="margin: 0; font-size: 15px; line-height: 1.6; font-weight: 600;">Psycheversity Research Team</p>
                </div>
                {footer_html}
                {unsubscribe_html}
            </div>
        </div>
    </body>
    </html>
    """
    text_content = '\n\n'.join(
        [subject, *paragraphs, 'Warm regards,\nPsycheversity Research Team', '',
         STANDARD_FOOTER['paragraphs_en'][0].format(**links),
         STANDARD_FOOTER['paragraphs_en'][1].format(**links),
         SIGN_OFF_EN,
         f'Unsubscribe / ان سبسکرائب کریں: {unsubscribe}']
    )
    return {'subject': subject, 'text_content': text_content, 'html_content': html_content,
            'unsubscribe_url': unsubscribe}
