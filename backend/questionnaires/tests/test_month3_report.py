"""
Legacy month-3 report tests — migrated to use send_perma_snapshot_report_task.
Comprehensive coverage has moved to test_perma_report.py.
These tests are kept for continuity and verify the 3_MONTHS milestone path specifically.
"""
import pytest
from django.core import mail
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch

from users.models import User, Role
from questionnaires.models import Questionnaire, Question, Option, ResponseSet, Response, PermaReportLog
from questionnaires.tasks import send_perma_snapshot_report_task
from questionnaires.serializers import ResponseSetSubmitSerializer


@pytest.fixture
def participant_role(db):
    return Role.objects.get_or_create(name='Participant')[0]


@pytest.fixture
def user(db, participant_role):
    return User.objects.create_user(
        username='test_participant',
        email='participant@test.com',
        password='password123',
        role=participant_role,
        has_completed_sociodemographic=True,
        onboarding_completed_at=timezone.now() - timedelta(days=90),
    )


@pytest.fixture
def psych_questionnaire(db):
    return Questionnaire.objects.create(
        title='Psychometric Battery',
        assessment_type='PSYCHOMETRIC',
        is_active=True,
    )


SCORES_3M = {
    'PERMA_P': 8.2, 'PERMA_E': 8.4, 'PERMA_R': 8.0, 'PERMA_M': 8.5,
    'PERMA_A': 8.3, 'PERMA_N': 2.5, 'PERMA_H': 8.5, 'PERMA_LON': 2.0,
    'PERMA_HAP': 8.0, 'PERMA_OVERALL': 8.5,
}


@pytest.mark.django_db(transaction=True)
class TestMonth3Report:

    def test_report_generation_and_email(self, user, psych_questionnaire):
        rs_3months = ResponseSet.objects.create(
            user=user, questionnaire=psych_questionnaire,
            status='COMPLETED', milestone='3_MONTHS',
            scores=SCORES_3M, completed_at=timezone.now(),
        )
        mail.outbox.clear()

        res = send_perma_snapshot_report_task.apply(args=[str(rs_3months.id), '3_MONTHS']).get()

        assert res['status'] == 'sent'
        assert res['recipient'] == 'participant@test.com'

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert email.to == ['participant@test.com']
        assert 'month-3' in email.subject.lower()
        assert len(email.attachments) == 1
        fname, pdf_data, mime = email.attachments[0]
        assert fname == 'pims_month3_report.pdf'
        assert mime == 'application/pdf'
        assert len(pdf_data) > 0

    @patch('questionnaires.tasks.send_perma_snapshot_report_task.delay')
    def test_submission_triggers_month3_report_task(self, mock_delay, user, psych_questionnaire):
        rs = ResponseSet.objects.create(
            user=user, questionnaire=psych_questionnaire,
            status='DRAFT', milestone='3_MONTHS',
        )
        serializer = ResponseSetSubmitSerializer(instance=rs, data={'responses_data': []})
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        mock_delay.assert_called_once_with(str(rs.id), '3_MONTHS')

    def test_report_generation_skipped_if_no_scores(self, user, psych_questionnaire):
        rs = ResponseSet.objects.create(
            user=user, questionnaire=psych_questionnaire,
            status='COMPLETED', milestone='3_MONTHS',
            scores={}, completed_at=timezone.now(),
        )
        mail.outbox.clear()

        res = send_perma_snapshot_report_task.apply(args=[str(rs.id), '3_MONTHS']).get()
        assert res['status'] == 'skipped'
        assert res['reason'] == 'no_scores'
        assert len(mail.outbox) == 0

    def test_report_generation_skipped_if_no_email(self, user, psych_questionnaire):
        user.email = ''
        user.save()
        rs = ResponseSet.objects.create(
            user=user, questionnaire=psych_questionnaire,
            status='COMPLETED', milestone='3_MONTHS',
            scores=SCORES_3M, completed_at=timezone.now(),
        )
        mail.outbox.clear()

        res = send_perma_snapshot_report_task.apply(args=[str(rs.id), '3_MONTHS']).get()
        assert res['status'] == 'skipped'
        assert res['reason'] == 'missing_email'
        assert len(mail.outbox) == 0

    def test_report_generation_with_malformed_scores(self, user, psych_questionnaire):
        bad = dict(SCORES_3M, PERMA_P='invalid_string', PERMA_M=None)
        rs = ResponseSet.objects.create(
            user=user, questionnaire=psych_questionnaire,
            status='COMPLETED', milestone='3_MONTHS',
            scores=bad, completed_at=timezone.now(),
        )
        mail.outbox.clear()

        res = send_perma_snapshot_report_task.apply(args=[str(rs.id), '3_MONTHS']).get()
        assert res['status'] == 'sent'
        assert len(mail.outbox) == 1
