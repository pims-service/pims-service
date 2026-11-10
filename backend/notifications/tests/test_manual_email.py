from datetime import timedelta

import pytest
from django.conf import settings
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from activities.models import Activity, Submission
from notifications.manual_email import eligible_recipients, make_unsubscribe_token, segment_recipients
from notifications.models import ManualEmailCampaign, Notification
from users.models import User

BEFORE = settings.EMAIL_CONSENT_REQUIRED_FROM - timedelta(days=5)
AFTER = settings.EMAIL_CONSENT_REQUIRED_FROM + timedelta(hours=1)


def _participant(username, created_at=BEFORE, **extra):
    fields = {'has_completed_sociodemographic': True, **extra}
    user = User.objects.create_user(
        username=username, email=f"{username}@example.com", password="pass1234", full_name=f"{username.title()} Test",
        **fields,
    )
    User.objects.filter(pk=user.pk).update(created_at=created_at)
    user.refresh_from_db()
    return user


@pytest.fixture
def admin_client(db):
    admin = User.objects.create_user(
        username="me_admin", email="admin@example.com", password="pass1234", is_staff=True,
    )
    client = APIClient()
    client.force_authenticate(admin)
    return client, admin


@pytest.mark.django_db
def test_eligibility_rules():
    old = _participant("me_old")
    new_no_consent = _participant("me_new_no", created_at=AFTER)
    new_consent = _participant("me_new_yes", created_at=AFTER, email_consent=True)
    unsubscribed = _participant("me_unsub", email_unsubscribed_at=timezone.now())
    disqualified = _participant("me_disq", is_disqualified=True)
    not_screened = _participant("me_unscreened", has_completed_sociodemographic=False)
    staff = _participant("me_staff", is_staff=True)

    ids = set(eligible_recipients().values_list('pk', flat=True))
    assert ids == {old.pk, new_consent.pk}
    # The model property agrees with the queryset for consent/unsubscribe.
    assert old.accepts_manual_emails and new_consent.accepts_manual_emails
    assert not new_no_consent.accepts_manual_emails and not unsubscribed.accepts_manual_emails
    for u in (disqualified, not_screened, staff):
        assert u.pk not in ids


@pytest.mark.django_db
def test_segments_not_started_and_stopped():
    never = _participant("me_never", created_at=timezone.now() - timedelta(days=3))
    too_new = _participant("me_toonew", created_at=timezone.now() - timedelta(hours=10))
    stopped = _participant("me_stopped")
    active = _participant("me_active")
    _submit(stopped, days_ago=5)
    _submit(active, days_ago=1)

    not_started = {u.pk for u in segment_recipients('not_started')}
    assert never.pk in not_started and too_new.pk not in not_started
    assert stopped.pk not in not_started and active.pk not in not_started

    stopped_ids = {u.pk for u in segment_recipients('stopped')}
    assert stopped_ids == {stopped.pk}

    picked = segment_recipients('manual', [never.pk, active.pk, 999999])
    assert {u.pk for u in picked} == {never.pk, active.pk}


def _phase():
    from phases.models import Phase
    return Phase.objects.first() or Phase.objects.create(
        phase_number=91, name="ME Phase", start_date=timezone.localdate(), end_date=timezone.localdate(),
    )


def _submit(user, days_ago):
    activity = Activity.objects.first()
    if activity is None:
        activity = Activity.objects.create(
            title="Day 1", description="", assigned_phase=_phase(), activity_type='paragraph', day_number=1,
        )
    sub = Submission.objects.create(user=user, activity=activity, content='entry', experiment_day=1)
    Submission.objects.filter(pk=sub.pk).update(submission_date=timezone.now() - timedelta(days=days_ago))


@pytest.mark.django_db
def test_send_flow_logs_history_and_skips_unsubscribed(admin_client):
    client, _ = admin_client
    a = _participant("me_a")
    b = _participant("me_b")

    preview = client.get(reverse('manual_email_recipients'), {'segment': 'all_eligible'})
    assert preview.status_code == 200 and preview.data['count'] == 2

    res = client.post(reverse('manual_email_send'), {
        'segment': 'manual', 'user_ids': [a.pk, b.pk], 'expected_count': 2,
        'subject': 'Hello {first_name}', 'body': 'Dear {first_name},\n\nPlease continue.',
    }, format='json')
    assert res.status_code == 202

    assert len(mail.outbox) == 2
    msg = next(m for m in mail.outbox if m.to == [a.email])
    assert msg.subject == 'Hello Me_A'
    html_part = msg.alternatives[0][0]
    assert 'Dear Me_A' in html_part and '/api/notifications/unsubscribe/' in html_part
    assert 'PIMS' not in html_part and 'PIMS' not in msg.body
    assert msg.extra_headers['List-Unsubscribe'].startswith('<')

    campaign = ManualEmailCampaign.objects.get(pk=res.data['campaign_id'])
    assert campaign.status == 'done'
    assert Notification.objects.filter(campaign=campaign, status='sent', n_type='email').count() == 2

    history = client.get(reverse('manual_email_history')).data
    assert history[0]['sent'] == 2 and history[0]['segment'] == 'manual'


@pytest.mark.django_db
def test_send_refuses_when_group_changed(admin_client):
    client, _ = admin_client
    _participant("me_c")
    res = client.post(reverse('manual_email_send'), {
        'segment': 'all_eligible', 'expected_count': 5, 'subject': 'S', 'body': 'B',
    }, format='json')
    assert res.status_code == 409
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_test_email_goes_to_team_inbox_only(admin_client):
    client, admin = admin_client
    _participant("me_d")
    res = client.post(reverse('manual_email_test'), {'subject': 'Test', 'body': 'Body'}, format='json')
    assert res.status_code == 202
    assert res.data['sent_to'] == settings.SUPPORT_ADMIN_EMAIL
    assert [m.to for m in mail.outbox] == [[settings.SUPPORT_ADMIN_EMAIL]]
    assert ManualEmailCampaign.objects.get(pk=res.data['campaign_id']).segment == 'test'


@pytest.mark.django_db
def test_participants_cannot_use_admin_endpoints():
    user = _participant("me_e")
    client = APIClient()
    client.force_authenticate(user)
    assert client.get(reverse('manual_email_recipients')).status_code == 403
    assert client.post(reverse('manual_email_send'), {}, format='json').status_code == 403


@pytest.mark.django_db
def test_unsubscribe_link_get_confirms_post_applies():
    user = _participant("me_f")
    url = reverse('manual_email_unsubscribe', kwargs={'token': make_unsubscribe_token(user)})
    client = APIClient()

    assert client.get(url).status_code == 200
    user.refresh_from_db()
    assert user.email_unsubscribed_at is None  # opening the link alone does nothing

    assert client.post(url).status_code == 200
    user.refresh_from_db()
    assert user.email_unsubscribed_at is not None and user.email_consent is False
    assert user.pk not in set(eligible_recipients().values_list('pk', flat=True))

    bad = reverse('manual_email_unsubscribe', kwargs={'token': 'tampered'})
    assert 'not valid' in client.post(bad).content.decode()


@pytest.mark.django_db
def test_profile_toggle_round_trip():
    user = _participant("me_g", created_at=AFTER)
    client = APIClient()
    client.force_authenticate(user)
    url = '/api/users/profile/'
    assert client.get(url).data['receive_study_emails'] is False
    assert client.patch(url, {'receive_study_emails': True}, format='json').data['receive_study_emails'] is True
    user.refresh_from_db()
    assert user.email_consent and user.email_consent_at is not None
    assert client.patch(url, {'receive_study_emails': False}, format='json').data['receive_study_emails'] is False
    user.refresh_from_db()
    assert user.email_unsubscribed_at is not None
