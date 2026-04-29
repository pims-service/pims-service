import pytest
from datetime import timedelta
from django.utils import timezone
from django.test import TestCase

from users.models import User, Role
from questionnaires.models import Questionnaire, Question, Option, ResponseSet, Response


@pytest.fixture
def participant_role(db):
    return Role.objects.create(name='Participant', description='Test participant')


@pytest.fixture
def baseline_questionnaire(db):
    q = Questionnaire.objects.create(
        title='Baseline Assessment',
        description='Initial screening',
        is_baseline=True,
        is_active=True,
    )
    question = Question.objects.create(
        questionnaire=q, content='How are you?', type='SCALE', order=1
    )
    Option.objects.create(question=question, label='Good', numeric_value=1, order=1)
    return q


@pytest.fixture
def posttest_questionnaire(db):
    q = Questionnaire.objects.create(
        title='Day 7 Post-Test',
        description='Post-test reassessment',
        is_posttest=True,
        is_active=True,
    )
    question = Question.objects.create(
        questionnaire=q, content='How are you now?', type='SCALE', order=1
    )
    Option.objects.create(question=question, label='Good', numeric_value=1, order=1)
    return q


@pytest.fixture
def user_before_day7(db, participant_role):
    """User who completed baseline but hasn't reached Day 7."""
    user = User.objects.create_user(
        username='early_user',
        email='early@test.com',
        password='testpass123',
        role=participant_role,
        has_completed_baseline=True,
        baseline_completed_at=timezone.now() - timedelta(days=3),
    )
    return user


@pytest.fixture
def user_at_day7(db, participant_role):
    """User who completed baseline and has reached Day 7."""
    user = User.objects.create_user(
        username='day7_user',
        email='day7@test.com',
        password='testpass123',
        role=participant_role,
        has_completed_baseline=True,
        baseline_completed_at=timezone.now() - timedelta(days=7),
    )
    return user


@pytest.fixture
def user_posttest_done(db, participant_role):
    """User who already completed the post-test."""
    user = User.objects.create_user(
        username='done_user',
        email='done@test.com',
        password='testpass123',
        role=participant_role,
        has_completed_baseline=True,
        baseline_completed_at=timezone.now() - timedelta(days=10),
        has_completed_posttest=True,
        posttest_completed_at=timezone.now() - timedelta(days=2),
    )
    return user


# --- is_posttest_due property tests ---

@pytest.mark.django_db
def test_posttest_not_due_before_day7(user_before_day7):
    """Post-test should NOT be due before Day 7."""
    assert user_before_day7.is_posttest_due is False


@pytest.mark.django_db
def test_posttest_due_at_day7(user_at_day7):
    """Post-test SHOULD be due at Day 7."""
    assert user_at_day7.is_posttest_due is True


@pytest.mark.django_db
def test_posttest_not_due_when_already_completed(user_posttest_done):
    """Post-test should NOT be due if already completed."""
    assert user_posttest_done.is_posttest_due is False


@pytest.mark.django_db
def test_posttest_not_due_without_baseline(db, participant_role):
    """Post-test should NOT be due if baseline is not completed."""
    user = User.objects.create_user(
        username='no_baseline',
        email='nobase@test.com',
        password='testpass123',
        role=participant_role,
        has_completed_baseline=False,
    )
    assert user.is_posttest_due is False


# --- Post-test submission tests ---

@pytest.mark.django_db
def test_posttest_submission_marks_completed(user_at_day7, posttest_questionnaire):
    """Submitting a post-test should mark user as having completed it."""
    from questionnaires.serializers import ResponseSetSubmitSerializer

    # Create a response set
    rs = ResponseSet.objects.create(
        user=user_at_day7,
        questionnaire=posttest_questionnaire,
        status='DRAFT',
    )

    # Get the question and option for the post-test
    question = posttest_questionnaire.questions.first()
    option = question.options.first()

    # Simulate submission
    serializer = ResponseSetSubmitSerializer(
        instance=rs,
        data={'responses_data': [{'question_id': str(question.id), 'selected_option_id': str(option.id)}]},
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()

    # Reload user from DB
    user_at_day7.refresh_from_db()
    assert user_at_day7.has_completed_posttest is True
    assert user_at_day7.posttest_completed_at is not None
    assert user_at_day7.is_posttest_due is False


# --- Questionnaire model tests ---

@pytest.mark.django_db
def test_questionnaire_is_posttest_field(posttest_questionnaire):
    """Verify the is_posttest field works correctly."""
    assert posttest_questionnaire.is_posttest is True


@pytest.mark.django_db
def test_baseline_is_not_posttest(baseline_questionnaire):
    """Baseline questionnaire should not be marked as post-test."""
    assert baseline_questionnaire.is_posttest is False
