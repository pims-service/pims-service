import html

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .manual_email import SEGMENT_LABELS, read_unsubscribe_token, segment_recipients
from .models import ManualEmailCampaign, Notification
from .serializers import NotificationSerializer
from users.permissions import OnboardingCompleted

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticated, OnboardingCompleted,)

    def get_queryset(self):
        # Manual (admin-sent) emails are logged as notifications but are not part of the in-app feed.
        return Notification.objects.filter(user=self.request.user, campaign__isnull=True)

class AdminScheduleNotificationView(generics.CreateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAdminUser,)


# ── Manual (admin-sent) emails ───────────────────────────────────────────────

MAX_SUBJECT_LENGTH = 200


def _validate_message(data):
    subject = (data.get('subject') or '').strip()
    body = (data.get('body') or '').strip()
    errors = {}
    if not subject:
        errors['subject'] = 'Subject is required.'
    elif len(subject) > MAX_SUBJECT_LENGTH:
        errors['subject'] = f'Subject must be at most {MAX_SUBJECT_LENGTH} characters.'
    if not body:
        errors['body'] = 'Message is required.'
    return subject, body, errors


def _parse_user_ids(raw):
    try:
        return [int(x) for x in (raw or [])]
    except (TypeError, ValueError):
        return None


class AdminManualEmailRecipientsView(APIView):
    """GET ?segment=<key>: how many (and which) participants a manual email would reach."""
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        segment = request.query_params.get('segment', 'all_eligible')
        if segment not in SEGMENT_LABELS:
            return Response({'detail': 'Unknown segment.'}, status=status.HTTP_400_BAD_REQUEST)
        # For "pick by hand" the list offered is everyone eligible.
        users = segment_recipients('all_eligible' if segment == 'manual' else segment)
        return Response({
            'segment': segment,
            'count': len(users),
            'recipients': [
                {'user_id': u.pk, 'name': u.full_name or u.username, 'email': u.email, 'joined': u.created_at}
                for u in users
            ],
        })


class AdminManualEmailTestView(APIView):
    """POST {subject, body}: sends the email to the team inbox (SUPPORT_ADMIN_EMAIL) only."""
    permission_classes = (permissions.IsAdminUser,)

    def post(self, request):
        from .tasks import send_manual_campaign_task

        subject, body, errors = _validate_message(request.data)
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        campaign = ManualEmailCampaign.objects.create(
            created_by=request.user, segment='test', subject=subject, body=body,
        )
        # Logged against the admin's account; delivered to SUPPORT_ADMIN_EMAIL (see send_manual_email_task).
        send_manual_campaign_task.delay(campaign.pk, [request.user.pk])
        return Response(
            {'campaign_id': campaign.pk, 'sent_to': settings.SUPPORT_ADMIN_EMAIL}, status=status.HTTP_202_ACCEPTED
        )


class AdminManualEmailSendView(APIView):
    """POST {segment, subject, body, user_ids?, expected_count}: queues the email to the segment."""
    permission_classes = (permissions.IsAdminUser,)

    def post(self, request):
        from .tasks import send_manual_campaign_task

        segment = request.data.get('segment')
        if segment not in SEGMENT_LABELS:
            return Response({'segment': 'Pick a group.'}, status=status.HTTP_400_BAD_REQUEST)
        subject, body, errors = _validate_message(request.data)
        user_ids = None
        if segment == 'manual':
            user_ids = _parse_user_ids(request.data.get('user_ids'))
            if not user_ids:
                errors['user_ids'] = 'Tick at least one person.'
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        count = len(segment_recipients(segment, user_ids))
        if count == 0:
            return Response({'detail': 'Nobody in this group can receive emails.'}, status=status.HTTP_400_BAD_REQUEST)
        # The admin confirmed "Send to N people?"; refuse if the group changed since then.
        expected = request.data.get('expected_count')
        if expected is not None and str(expected) != str(count):
            return Response(
                {'detail': f'The group now has {count} people (you confirmed {expected}). Please check and confirm again.',
                 'count': count},
                status=status.HTTP_409_CONFLICT,
            )

        campaign = ManualEmailCampaign.objects.create(
            created_by=request.user, segment=segment, subject=subject, body=body, recipient_count=count,
        )
        send_manual_campaign_task.delay(campaign.pk, user_ids)
        return Response({'campaign_id': campaign.pk, 'count': count}, status=status.HTTP_202_ACCEPTED)


class AdminManualEmailHistoryView(APIView):
    """GET: sent history (newest first)."""
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        campaigns = (
            ManualEmailCampaign.objects.select_related('created_by')
            .annotate(
                sent=Count('notifications', filter=Q(notifications__status='sent')),
                failed=Count('notifications', filter=Q(notifications__status='failed')),
                pending=Count('notifications', filter=Q(notifications__status='pending')),
            )[:100]
        )
        return Response([
            {
                'id': c.pk,
                'created_at': c.created_at,
                'segment': c.segment,
                'segment_label': c.get_segment_display(),
                'subject': c.subject,
                'recipient_count': c.recipient_count,
                'sent': c.sent,
                'failed': c.failed,
                'pending': c.pending,
                'status': c.status,
                'sent_by': (c.created_by.full_name or c.created_by.username) if c.created_by else None,
            }
            for c in campaigns
        ])


def _unsubscribe_page(title, message, form_action=None):
    button = ''
    if form_action:
        button = (
            f'<form method="post" action="{html.escape(form_action)}">'
            '<button type="submit" style="background:#2E4E90;color:#fff;border:0;border-radius:6px;'
            'padding:12px 22px;font-size:15px;cursor:pointer;">Unsubscribe / ان سبسکرائب کریں</button></form>'
        )
    return HttpResponse(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Psycheversity</title></head>
<body style="margin:0;background:#f4f4f5;font-family:Arial,Helvetica,sans-serif;color:#18181b;">
<div style="max-width:520px;margin:48px auto;padding:0 16px;">
<div style="background:#fff;border:1px solid #e4e4e7;border-radius:8px;padding:28px;text-align:center;">
<h1 style="margin:0 0 14px;font-size:22px;color:#2E4E90;">Psycheversity</h1>
<h2 style="margin:0 0 12px;font-size:18px;">{title}</h2>
<p style="margin:0 0 20px;line-height:1.7;color:#3f3f46;">{message}</p>
{button}
</div></div></body></html>""")


INVALID_LINK = ('Link not valid', 'This unsubscribe link is not valid. / یہ لنک درست نہیں ہے۔')
UNSUBSCRIBED = (
    'You are unsubscribed',
    'You will not receive these study emails any more. You can turn them back on from your profile page. '
    '/ آپ کو یہ ای میلز اب نہیں بھیجی جائیں گی۔ آپ اپنے پروفائل سے انہیں دوبارہ آن کر سکتے ہیں۔',
)


@method_decorator(csrf_exempt, name='dispatch')
class UnsubscribeView(View):
    """
    Public link in every manual email. GET shows a confirm button (so link scanners that
    open URLs don't unsubscribe people); POST (the button, or a mail app's one-click
    List-Unsubscribe) applies it.
    """

    def _user(self, token):
        user_id = read_unsubscribe_token(token)
        if user_id is None:
            return None
        return get_user_model().objects.filter(pk=user_id).first()

    def get(self, request, token):
        user = self._user(token)
        if user is None:
            return _unsubscribe_page(*INVALID_LINK)
        if user.email_unsubscribed_at:
            return _unsubscribe_page(*UNSUBSCRIBED)
        return _unsubscribe_page(
            'Stop receiving these emails?',
            'Press the button to stop emails from the Psycheversity team. Reminders for your study assessments '
            'are not affected. / ای میلز بند کرنے کے لیے بٹن دبائیں۔',
            form_action=request.path,
        )

    def post(self, request, token):
        user = self._user(token)
        if user is None:
            return _unsubscribe_page(*INVALID_LINK)
        if not user.email_unsubscribed_at:
            user.set_email_consent(False)
        return _unsubscribe_page(*UNSUBSCRIBED)
