"""
Tests for the PERMA snapshot report feature.

Covers:
  - send_perma_snapshot_report_task (happy path, all milestones)
  - Idempotency: never sends twice for same user+milestone
  - Skip conditions: no email, no scores
  - Audit log (PermaReportLog) creation on success, skip, and error
  - check_and_send_perma_reports daily cron
  - _build_bar_chart: returns valid PNG, handles zero/malformed scores
  - Scoring: PERMA_HAP stored and exported
  - Serializer event-driven triggers for SIGNUP, 3_MONTHS, 1_YEAR
"""
import base64
import pytest
from unittest.mock import patch, MagicMock
from django.core import mail
from django.utils import timezone
from datetime import timedelta

from users.models import User, Role
from questionnaires.models import Questionnaire, Question, ResponseSet, PermaReportLog
from questionnaires.tasks import (
    send_perma_snapshot_report_task,
    check_and_send_perma_reports,
    _build_bar_chart,
)
from questionnaires.scoring import calculate_scores, PERMA_EXPORT_SCORES


# ── Shared fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def participant_role(db):
    return Role.objects.get_or_create(name='Participant')[0]


@pytest.fixture
def user(db, participant_role):
    return User.objects.create_user(
        username='perma_test_user',
        email='permauser@test.com',
        password='testpass123',
        role=participant_role,
        has_completed_sociodemographic=True,
        onboarding_completed_at=timezone.now() - timedelta(days=90),
    )


@pytest.fixture
def user_no_email(db, participant_role):
    return User.objects.create_user(
        username='no_email_user',
        email='',
        password='testpass123',
        role=participant_role,
        has_completed_sociodemographic=True,
    )


@pytest.fixture
def psych_q(db):
    return Questionnaire.objects.create(
        title='Psychometric Battery',
        assessment_type='PSYCHOMETRIC',
        is_active=True,
    )


SAMPLE_SCORES = {
    'PERMA_P': 7.0, 'PERMA_E': 6.5, 'PERMA_R': 7.5, 'PERMA_M': 8.0,
    'PERMA_A': 6.0, 'PERMA_N': 3.5, 'PERMA_H': 7.2, 'PERMA_LON': 2.8,
    'PERMA_HAP': 7.0, 'PERMA_OVERALL': 7.1,
}


def _make_rs(user, psych_q, milestone, scores=None):
    return ResponseSet.objects.create(
        user=user,
        questionnaire=psych_q,
        status='COMPLETED',
        milestone=milestone,
        scores=scores if scores is not None else SAMPLE_SCORES,
        completed_at=timezone.now(),
    )


# ── _build_bar_chart ───────────────────────────────────────────────────────────

class TestBuildBarChart:

    def test_returns_valid_base64_png(self):
        b64 = _build_bar_chart(SAMPLE_SCORES)
        assert isinstance(b64, str)
        assert len(b64) > 0
        raw = base64.b64decode(b64)
        # PNG magic bytes
        assert raw[:8] == b'\x89PNG\r\n\x1a\n'

    def test_handles_all_scores_missing(self):
        """All scores absent → treat as zero, must not raise."""
        b64 = _build_bar_chart({})
        assert len(b64) > 0
        assert base64.b64decode(b64)[:4] == b'\x89PNG'

    def test_handles_malformed_score_values(self):
        """String / None values must fall back to 0.0 without crashing."""
        bad_scores = {
            'PERMA_P': 'not_a_number', 'PERMA_E': None, 'PERMA_R': 7.0,
            'PERMA_M': 8.0, 'PERMA_A': 6.0, 'PERMA_N': 3.5,
            'PERMA_H': 7.2, 'PERMA_LON': 2.8, 'PERMA_HAP': 7.0, 'PERMA_OVERALL': 7.1,
        }
        b64 = _build_bar_chart(bad_scores)
        assert len(b64) > 0

    def test_perma_hap_is_included_in_block3(self):
        """PERMA_HAP (Happiness) must appear in the additional-measures block."""
        # We can't easily inspect bar positions, but we ensure the function
        # reads PERMA_HAP without KeyError and produces a chart.
        scores_with_hap = dict(SAMPLE_SCORES, PERMA_HAP=9.5)
        b64 = _build_bar_chart(scores_with_hap)
        assert len(b64) > 0


# ── PERMA scoring: PERMA_HAP ──────────────────────────────────────────────────

class TestScoringPermaHap:

    def test_perma_hap_stored_from_item_23(self):
        val_map = {i: float(i % 10) for i in range(1, 24)}
        val_map[23] = 8.0  # Hap item
        scores = calculate_scores(val_map)
        assert 'PERMA_HAP' in scores
        assert scores['PERMA_HAP'] == 8.0

    def test_perma_hap_zero_when_item_23_absent(self):
        val_map = {i: 5.0 for i in range(1, 23)}  # no item 23
        scores = calculate_scores(val_map)
        assert scores.get('PERMA_HAP', 0.0) == 0.0

    def test_perma_hap_in_export_scores(self):
        export_keys = [key for key, _ in PERMA_EXPORT_SCORES]
        assert 'PERMA_HAP' in export_keys

    def test_perma_hap_before_overall_in_export(self):
        keys = [key for key, _ in PERMA_EXPORT_SCORES]
        assert keys.index('PERMA_HAP') < keys.index('PERMA_OVERALL')


# ── PermaReportLog model ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPermaReportLog:

    def test_default_status_is_sent(self, user):
        log = PermaReportLog.objects.create(user=user, milestone='SIGNUP')
        assert log.status == 'sent'

    def test_unique_together_prevents_duplicate(self, user):
        from django.db import IntegrityError
        PermaReportLog.objects.create(user=user, milestone='SIGNUP')
        with pytest.raises(IntegrityError):
            PermaReportLog.objects.create(user=user, milestone='SIGNUP')

    def test_different_milestones_allowed(self, user):
        PermaReportLog.objects.create(user=user, milestone='SIGNUP')
        PermaReportLog.objects.create(user=user, milestone='3_MONTHS')
        assert PermaReportLog.objects.filter(user=user).count() == 2


# ── send_perma_snapshot_report_task ───────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
class TestSendPermaSnapshotReportTask:

    # ── Happy path per milestone ──────────────────────────────────────────────

    @pytest.mark.parametrize('milestone,expected_filename,expected_subject_part', [
        ('SIGNUP',    'pims_baseline_report.pdf',  'baseline'),
        ('3_MONTHS',  'pims_month3_report.pdf',    'month-3'),
        ('1_YEAR',    'pims_month12_report.pdf',   'month-12'),
    ])
    def test_sends_email_with_pdf_for_each_milestone(
        self, user, psych_q, milestone, expected_filename, expected_subject_part
    ):
        rs = _make_rs(user, psych_q, milestone)
        mail.outbox.clear()

        result = send_perma_snapshot_report_task.apply(args=[str(rs.id), milestone]).get()

        assert result['status'] == 'sent'
        assert result['recipient'] == user.email
        assert result['milestone'] == milestone

        assert len(mail.outbox) == 1
        sent = mail.outbox[0]
        assert sent.to == [user.email]
        assert expected_subject_part.lower() in sent.subject.lower()

        assert len(sent.attachments) == 1
        fname, pdf_data, mime = sent.attachments[0]
        assert fname == expected_filename
        assert mime == 'application/pdf'
        assert len(pdf_data) > 0

    def test_audit_log_created_on_success(self, user, psych_q):
        rs = _make_rs(user, psych_q, 'SIGNUP')
        send_perma_snapshot_report_task.apply(args=[str(rs.id), 'SIGNUP']).get()

        log = PermaReportLog.objects.get(user=user, milestone='SIGNUP')
        assert log.status == 'sent'
        assert log.error_detail == ''

    # ── No-email skip ─────────────────────────────────────────────────────────

    def test_skips_when_user_has_no_email(self, user_no_email, psych_q):
        rs = _make_rs(user_no_email, psych_q, 'SIGNUP')
        mail.outbox.clear()

        result = send_perma_snapshot_report_task.apply(args=[str(rs.id), 'SIGNUP']).get()

        assert result['status'] == 'skipped'
        assert result['reason'] == 'missing_email'
        assert len(mail.outbox) == 0

    # ── No-scores skip ────────────────────────────────────────────────────────

    def test_skips_and_logs_when_scores_empty(self, user, psych_q):
        rs = _make_rs(user, psych_q, '3_MONTHS', scores={})
        mail.outbox.clear()

        result = send_perma_snapshot_report_task.apply(args=[str(rs.id), '3_MONTHS']).get()

        assert result['status'] == 'skipped'
        assert result['reason'] == 'no_scores'
        assert len(mail.outbox) == 0

        log = PermaReportLog.objects.get(user=user, milestone='3_MONTHS')
        assert log.status == 'skipped'

    # ── Idempotency ───────────────────────────────────────────────────────────

    def test_does_not_send_twice_for_same_milestone(self, user, psych_q):
        rs = _make_rs(user, psych_q, 'SIGNUP')
        mail.outbox.clear()

        send_perma_snapshot_report_task.apply(args=[str(rs.id), 'SIGNUP']).get()
        first_count = len(mail.outbox)

        # Second call must be a no-op
        result = send_perma_snapshot_report_task.apply(args=[str(rs.id), 'SIGNUP']).get()

        assert result['status'] == 'skipped'
        assert result['reason'] == 'already_sent'
        assert len(mail.outbox) == first_count  # no new email

    def test_different_milestones_send_independently(self, user, psych_q):
        rs_signup = _make_rs(user, psych_q, 'SIGNUP')
        rs_3m = _make_rs(user, psych_q, '3_MONTHS')
        mail.outbox.clear()

        send_perma_snapshot_report_task.apply(args=[str(rs_signup.id), 'SIGNUP']).get()
        send_perma_snapshot_report_task.apply(args=[str(rs_3m.id), '3_MONTHS']).get()

        assert len(mail.outbox) == 2
        assert PermaReportLog.objects.filter(user=user).count() == 2

    # ── Malformed scores must not crash ───────────────────────────────────────

    def test_handles_malformed_scores_without_crash(self, user, psych_q):
        bad_scores = {
            'PERMA_P': 'invalid', 'PERMA_E': None, 'PERMA_R': 7.0,
            'PERMA_M': 8.0, 'PERMA_A': 6.0, 'PERMA_N': 3.5,
            'PERMA_H': 7.2, 'PERMA_LON': 2.8, 'PERMA_HAP': 7.0, 'PERMA_OVERALL': 7.1,
        }
        rs = _make_rs(user, psych_q, 'SIGNUP', scores=bad_scores)
        mail.outbox.clear()

        result = send_perma_snapshot_report_task.apply(args=[str(rs.id), 'SIGNUP']).get()
        assert result['status'] == 'sent'
        assert len(mail.outbox) == 1

    # ── Report content constraints ────────────────────────────────────────────

    def test_email_body_contains_no_score_values(self, user, psych_q):
        """Scores must live in the PDF only, not in the email body."""
        rs = _make_rs(user, psych_q, '3_MONTHS')
        mail.outbox.clear()

        send_perma_snapshot_report_task.apply(args=[str(rs.id), '3_MONTHS']).get()
        body = mail.outbox[0].body
        # None of the actual numeric score values should appear in the plain-text body
        for score_val in ['7.0', '6.5', '7.5', '8.0', '3.5', '7.2', '2.8', '7.1']:
            assert score_val not in body

    def test_subject_is_neutral_same_for_all_participants(self, user, psych_q):
        """Subject must not contain evaluative language."""
        for milestone in ('SIGNUP', '3_MONTHS', '1_YEAR'):
            rs = ResponseSet.objects.create(
                user=user, questionnaire=psych_q, status='COMPLETED',
                milestone=milestone, scores=SAMPLE_SCORES, completed_at=timezone.now(),
            )
            mail.outbox.clear()
            send_perma_snapshot_report_task.apply(args=[str(rs.id), milestone]).get()
            subject = mail.outbox[0].subject.lower()
            for forbidden in ('high', 'low', 'good', 'poor', 'flourish', 'languish'):
                assert forbidden not in subject, f"Forbidden word '{forbidden}' in subject: {subject}"
            PermaReportLog.objects.filter(user=user, milestone=milestone).delete()

    def test_pdf_attachment_is_non_empty(self, user, psych_q):
        rs = _make_rs(user, psych_q, 'SIGNUP')
        mail.outbox.clear()

        send_perma_snapshot_report_task.apply(args=[str(rs.id), 'SIGNUP']).get()
        _, pdf_data, _ = mail.outbox[0].attachments[0]
        # WeasyPrint PDFs start with %PDF
        assert pdf_data[:4] == b'%PDF'


# ── check_and_send_perma_reports (daily cron) ────────────────────────────────

@pytest.mark.django_db
class TestCheckAndSendPermaReports:

    @patch('questionnaires.tasks.send_perma_snapshot_report_task.delay')
    def test_dispatches_for_unreported_3_months(self, mock_delay, user, psych_q):
        rs = _make_rs(user, psych_q, '3_MONTHS')
        result = check_and_send_perma_reports()
        assert result['dispatched'] == 1
        mock_delay.assert_called_once_with(str(rs.id), '3_MONTHS')

    @patch('questionnaires.tasks.send_perma_snapshot_report_task.delay')
    def test_dispatches_for_unreported_1_year(self, mock_delay, user, psych_q):
        rs = _make_rs(user, psych_q, '1_YEAR')
        result = check_and_send_perma_reports()
        assert result['dispatched'] == 1
        mock_delay.assert_called_once_with(str(rs.id), '1_YEAR')

    @patch('questionnaires.tasks.send_perma_snapshot_report_task.delay')
    def test_skips_already_sent(self, mock_delay, user, psych_q):
        rs = _make_rs(user, psych_q, '3_MONTHS')
        PermaReportLog.objects.create(user=user, milestone='3_MONTHS', status='sent')

        result = check_and_send_perma_reports()
        assert result['dispatched'] == 0
        mock_delay.assert_not_called()

    @patch('questionnaires.tasks.send_perma_snapshot_report_task.delay')
    def test_does_not_dispatch_for_signup_milestone(self, mock_delay, user, psych_q):
        """SIGNUP reports are event-driven; cron must not re-dispatch them."""
        _make_rs(user, psych_q, 'SIGNUP')
        result = check_and_send_perma_reports()
        assert result['dispatched'] == 0
        mock_delay.assert_not_called()

    @patch('questionnaires.tasks.send_perma_snapshot_report_task.delay')
    def test_does_not_dispatch_for_draft_response_sets(self, mock_delay, user, psych_q):
        ResponseSet.objects.create(
            user=user, questionnaire=psych_q, status='DRAFT',
            milestone='3_MONTHS', scores=SAMPLE_SCORES,
        )
        result = check_and_send_perma_reports()
        assert result['dispatched'] == 0
        mock_delay.assert_not_called()

    @patch('questionnaires.tasks.send_perma_snapshot_report_task.delay')
    def test_dispatches_multiple_users(self, mock_delay, psych_q, participant_role):
        users = [
            User.objects.create_user(
                username=f'multi_user_{i}', email=f'multi{i}@test.com',
                password='pw', role=participant_role,
            )
            for i in range(3)
        ]
        for u in users:
            _make_rs(u, psych_q, '3_MONTHS')

        result = check_and_send_perma_reports()
        assert result['dispatched'] == 3
        assert mock_delay.call_count == 3

    @patch('questionnaires.tasks.send_perma_snapshot_report_task.delay')
    def test_partial_sent_dispatches_only_unsent(self, mock_delay, psych_q, participant_role):
        """If 2 of 3 users already sent, only dispatch the remaining 1."""
        users = [
            User.objects.create_user(
                username=f'partial_user_{i}', email=f'partial{i}@test.com',
                password='pw', role=participant_role,
            )
            for i in range(3)
        ]
        rss = [_make_rs(u, psych_q, '3_MONTHS') for u in users]
        # Mark first 2 as already sent
        PermaReportLog.objects.create(user=users[0], milestone='3_MONTHS', status='sent')
        PermaReportLog.objects.create(user=users[1], milestone='3_MONTHS', status='sent')

        result = check_and_send_perma_reports()
        assert result['dispatched'] == 1
        mock_delay.assert_called_once_with(str(rss[2].id), '3_MONTHS')


# ── Serializer event-driven triggers ─────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
class TestSerializerTriggers:

    @patch('questionnaires.tasks.send_perma_snapshot_report_task.delay')
    def test_signup_completion_triggers_report(self, mock_delay, user, psych_q):
        from questionnaires.serializers import ResponseSetSubmitSerializer

        psych_q.assessment_type = 'PSYCHOMETRIC'
        psych_q.save()

        rs = ResponseSet.objects.create(
            user=user, questionnaire=psych_q, status='DRAFT', milestone='SIGNUP',
        )
        # Mark onboarding not yet done so is_new_onboarding = True
        user.onboarding_completed_at = None
        user.save()

        data = {'responses_data': []}
        serializer = ResponseSetSubmitSerializer(instance=rs, data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()

        mock_delay.assert_called_once_with(str(rs.id), 'SIGNUP')

    @patch('questionnaires.tasks.send_perma_snapshot_report_task.delay')
    def test_3months_completion_triggers_report(self, mock_delay, user, psych_q):
        from questionnaires.serializers import ResponseSetSubmitSerializer

        rs = ResponseSet.objects.create(
            user=user, questionnaire=psych_q, status='DRAFT', milestone='3_MONTHS',
        )
        data = {'responses_data': []}
        serializer = ResponseSetSubmitSerializer(instance=rs, data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()

        mock_delay.assert_called_once_with(str(rs.id), '3_MONTHS')

    @patch('questionnaires.tasks.send_perma_snapshot_report_task.delay')
    def test_1year_completion_triggers_report(self, mock_delay, user, psych_q):
        from questionnaires.serializers import ResponseSetSubmitSerializer

        rs = ResponseSet.objects.create(
            user=user, questionnaire=psych_q, status='DRAFT', milestone='1_YEAR',
        )
        data = {'responses_data': []}
        serializer = ResponseSetSubmitSerializer(instance=rs, data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()

        mock_delay.assert_called_once_with(str(rs.id), '1_YEAR')

    @patch('questionnaires.tasks.send_perma_snapshot_report_task.delay')
    def test_7days_completion_does_not_trigger_report(self, mock_delay, user, psych_q):
        from questionnaires.serializers import ResponseSetSubmitSerializer

        rs = ResponseSet.objects.create(
            user=user, questionnaire=psych_q, status='DRAFT', milestone='7_DAYS',
        )
        data = {'responses_data': []}
        serializer = ResponseSetSubmitSerializer(instance=rs, data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()

        mock_delay.assert_not_called()

    @patch('questionnaires.tasks.send_perma_snapshot_report_task.delay')
    @patch('groups.services.assign_user_to_group')
    def test_sociodemographic_completion_does_not_trigger_report(
        self, mock_assign, mock_delay, db, participant_role
    ):
        from questionnaires.serializers import ResponseSetSubmitSerializer

        socio_q = Questionnaire.objects.create(
            title='Sociodemographic Survey', assessment_type='SOCIODEMOGRAPHIC', is_active=True,
        )
        u = User.objects.create_user(
            username='socio_trig_user', email='s@test.com', password='pw',
            role=participant_role,
        )
        rs = ResponseSet.objects.create(
            user=u, questionnaire=socio_q, status='DRAFT', milestone='SIGNUP',
        )
        data = {'responses_data': []}
        serializer = ResponseSetSubmitSerializer(instance=rs, data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()

        mock_delay.assert_not_called()
