import pytest
from activities.models import Activity, Submission

@pytest.mark.django_db
def test_activity_creation(test_phase):
    activity = Activity.objects.create(
        title="Gratitude Journal",
        description="Write three things you are grateful for.",
        assigned_phase=test_phase,
        activity_type="paragraph"
    )
    assert activity.title == "Gratitude Journal"
    assert str(activity) == "Gratitude Journal"

@pytest.mark.django_db
def test_submission_creation(test_user, test_phase):
    activity = Activity.objects.create(
        title="Journal",
        description="Write.",
        assigned_phase=test_phase,
        activity_type="paragraph"
    )
    submission = Submission.objects.create(
        user=test_user,
        activity=activity,
        content="I am grateful for tests."
    )
    assert submission.content == "I am grateful for tests."
    assert str(submission) == f"{test_user.username} - Journal"
