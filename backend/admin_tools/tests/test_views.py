import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
from django.utils import timezone
from admin_tools.models import ExportTask
from activities.models import Activity, Submission
from questionnaires.models import Questionnaire, ResponseSet
from groups.models import Group
from phases.models import Phase


# ---------------------------------------------------------------------------
# Existing CSV Export Tests (unchanged)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_admin_export_csv(admin_client, test_user):
    url = reverse('export_csv')
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response['Content-Type'] == 'text/csv'
    assert 'experiment_data_spss.csv' in response['Content-Disposition']





@pytest.mark.django_db
@patch('admin_tools.views.generate_posttest_export_csv.delay')
def test_admin_export_t0_csv(mock_delay, admin_client):
    url = reverse('export_t0_csv')
    response = admin_client.post(url, {'group': 'Control'})

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert 'task_id' in response.data
    assert response.data['status'] == 'PENDING'

    task_id = response.data['task_id']
    task = ExportTask.objects.get(id=task_id)
    assert task.filters.get('group') == 'Control'
    mock_delay.assert_called_once_with(task.id)


@pytest.mark.django_db
@patch('admin_tools.views.generate_t1_export_csv.delay')
def test_admin_export_t1_csv(mock_delay, admin_client):
    url = reverse('export_t1_csv')
    response = admin_client.post(url, {'group': 'Control'})

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert 'task_id' in response.data
    assert response.data['status'] == 'PENDING'

    task_id = response.data['task_id']
    task = ExportTask.objects.get(id=task_id)
    assert task.filters.get('group') == 'Control'
    mock_delay.assert_called_once_with(task.id)


@pytest.mark.django_db
def test_admin_export_task_status_success(admin_client, admin_user):
    task = ExportTask.objects.create(user=admin_user, status='SUCCESS')
    url = reverse('export_task_status', kwargs={'task_id': task.id})
    response = admin_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == 'SUCCESS'
    assert response.data['id'] == str(task.id)


# ---------------------------------------------------------------------------
# AdminDashboardAnalyticsView — Tests for the optimised query rewrite
# ---------------------------------------------------------------------------

@pytest.fixture
def analytics_setup(db, admin_user, test_phase):
    """
    Creates a minimal but realistic dataset:
    - 2 participant users in different groups
    - 1 baseline questionnaire with 1 completed ResponseSet each
    - 1 daily activity with 1 Submission for user_a
    """
    group_a = Group.objects.create(name='Group A', capacity=20)
    group_b = Group.objects.create(name='Group B', capacity=20)

    from users.models import User
    user_a = User.objects.create_user(
        username='user_a', email='a@test.com', password='pass',
        group=group_a, has_completed_sociodemographic=True,
        onboarding_completed_at=timezone.now()
    )
    user_b = User.objects.create_user(
        username='user_b', email='b@test.com', password='pass',
        group=group_b, has_completed_sociodemographic=True,
        onboarding_completed_at=timezone.now()
    )

    questionnaire = Questionnaire.objects.create(title='Baseline', assessment_type='SOCIODEMOGRAPHIC', is_active=True)
    rs_a = ResponseSet.objects.create(user=user_a, questionnaire=questionnaire, status='COMPLETED', completed_at=timezone.now())
    rs_b = ResponseSet.objects.create(user=user_b, questionnaire=questionnaire, status='COMPLETED', completed_at=timezone.now())

    activity = Activity.objects.create(
        title='Day 1 Activity', description='Write.', assigned_phase=test_phase,
        group=group_a, activity_type='paragraph', day_number=1
    )
    sub = Submission.objects.create(
        user=user_a, activity=activity, content='My reflection.', experiment_day=1
    )

    return {
        'user_a': user_a, 'user_b': user_b,
        'group_a': group_a, 'group_b': group_b,
        'rs_a': rs_a, 'rs_b': rs_b,
        'submission': sub,
        'questionnaire': questionnaire,
    }


@pytest.mark.django_db
def test_dashboard_analytics_requires_admin(api_client, test_user):
    """Non-admin users must be rejected with 403."""
    api_client.force_authenticate(user=test_user)
    url = reverse('dashboard_analytics')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_dashboard_analytics_total_participants(admin_client, analytics_setup):
    """total_participants must count only non-superuser accounts."""
    url = reverse('dashboard_analytics')
    response = admin_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    # analytics_setup creates 2 regular users; admin_user is a superuser (excluded)
    assert response.data['total_participants'] == 2


@pytest.mark.django_db
def test_dashboard_analytics_total_submissions(admin_client, analytics_setup):
    """total_submissions = completed baselines + activity submissions."""
    url = reverse('dashboard_analytics')
    response = admin_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    # 2 completed response sets + 1 activity submission = 3
    assert response.data['total_submissions'] == 3


@pytest.mark.django_db
def test_dashboard_analytics_active_rate(admin_client, analytics_setup):
    """Both users completed baseline recently, so active rate must be 100%."""
    url = reverse('dashboard_analytics')
    response = admin_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['active_rate_percentage'] == 100.0


@pytest.mark.django_db
def test_dashboard_analytics_engagement_trend_shape(admin_client, analytics_setup):
    """Engagement trend must always return exactly 7 entries."""
    url = reverse('dashboard_analytics')
    response = admin_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    trend = response.data['engagement_trend']
    assert len(trend) == 7
    for entry in trend:
        assert 'date' in entry
        assert 'count' in entry
        assert isinstance(entry['count'], int)


@pytest.mark.django_db
def test_dashboard_analytics_engagement_trend_counts(admin_client, analytics_setup):
    """Today's trend count must include baselines + the activity submission."""
    url = reverse('dashboard_analytics')
    response = admin_client.get(url)

    trend = response.data['engagement_trend']
    today_entry = trend[-1]  # last entry is today
    # 2 completed response sets + 1 submission were all created today
    assert today_entry['count'] >= 3


@pytest.mark.django_db
def test_dashboard_analytics_recent_participants_shape(admin_client, analytics_setup):
    """Recent participants list must include required keys and group names."""
    url = reverse('dashboard_analytics')
    response = admin_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    participants = response.data['recent_participants']
    assert len(participants) == 2

    usernames = {p['username'] for p in participants}
    assert 'user_a' in usernames
    assert 'user_b' in usernames

    for p in participants:
        assert 'id' in p
        assert 'username' in p
        assert 'group' in p
        assert 'submissions_count' in p
        assert 'status' in p
        assert p['group'] != 'Unassigned'


@pytest.mark.django_db
def test_dashboard_analytics_submissions_count_per_user(admin_client, analytics_setup):
    """
    user_a: 1 completed baseline + 1 activity submission = 2 total -> "2/9"
    user_b: 1 completed baseline + 0 activity submissions = 1 total -> "1/9"
    """
    url = reverse('dashboard_analytics')
    response = admin_client.get(url)

    participants = {p['username']: p for p in response.data['recent_participants']}
    assert participants['user_a']['submissions_count'] == '2/9'
    assert participants['user_b']['submissions_count'] == '1/9'


@pytest.mark.django_db
def test_dashboard_analytics_inactive_user(admin_client, analytics_setup):
    """A user with no submissions must appear as Inactive in recent participants."""
    from users.models import User
    User.objects.create_user(
        username='inactive_user', email='inactive@test.com', password='pass',
        group=analytics_setup['group_a'], has_completed_sociodemographic=False
    )
    url = reverse('dashboard_analytics')
    response = admin_client.get(url)

    participants = {p['username']: p for p in response.data['recent_participants']}
    if 'inactive_user' in participants:
        assert participants['inactive_user']['status'] == 'Inactive'


# ---------------------------------------------------------------------------
# DB Index verification — ensure indexes are declared on the model Meta
# ---------------------------------------------------------------------------

def test_submission_model_has_user_date_index():
    """Compound index on (user, submission_date) must be declared."""
    from activities.models import Submission
    index_names = [idx.name for idx in Submission._meta.indexes]
    assert 'idx_submission_user_date' in index_names


def test_submission_experiment_day_has_db_index():
    """experiment_day field must carry db_index=True."""
    from activities.models import Submission
    field = Submission._meta.get_field('experiment_day')
    assert field.db_index is True


def test_submission_submission_date_has_db_index():
    """submission_date field must carry db_index=True."""
    from activities.models import Submission
    field = Submission._meta.get_field('submission_date')
    assert field.db_index is True


def test_responseset_has_status_completed_index():
    """Compound index on (status, completed_at) must be declared."""
    from questionnaires.models import ResponseSet
    index_names = [idx.name for idx in ResponseSet._meta.indexes]
    assert 'idx_rs_status_completed' in index_names


def test_responseset_has_user_status_index():
    """Compound index on (user, status) must be declared."""
    from questionnaires.models import ResponseSet
    index_names = [idx.name for idx in ResponseSet._meta.indexes]
    assert 'idx_rs_user_status' in index_names


@pytest.mark.django_db
def test_admin_export_longitudinal_csv(admin_client):
    url = reverse('export_longitudinal_csv')
    with patch('admin_tools.views.generate_longitudinal_export_csv.delay') as mock_delay:
        response = admin_client.post(url, {'group': 'All'})

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert 'task_id' in response.data
        assert response.data['status'] == 'PENDING'

        task_id = response.data['task_id']
        task = ExportTask.objects.get(id=task_id)
        assert task.filters.get('group') == 'All'
        mock_delay.assert_called_once_with(task.id)


@pytest.mark.django_db
def test_generate_longitudinal_export_csv_task(admin_user, test_group):
    from admin_tools.tasks import generate_longitudinal_export_csv
    from questionnaires.models import Questionnaire, Question, Option, ResponseSet, Response
    from django.utils import timezone

    # 1. Create a sociodemographic questionnaire and questions
    socio_q = Questionnaire.objects.create(
        title="Socio Survey", assessment_type='SOCIODEMOGRAPHIC', is_active=True
    )
    gender_q = Question.objects.create(
        questionnaire=socio_q, content="What is your gender?", type="CHOICE", order=1
    )
    opt_male = Option.objects.create(question=gender_q, label="Male", numeric_value=1, order=1)

    # 2. Create a psychometric questionnaire and questions
    psy_q = Questionnaire.objects.create(
        title="Battery", assessment_type='PSYCHOMETRIC', is_active=True
    )
    perma_q = Question.objects.create(
        questionnaire=psy_q, content="[PERMA] Feel joyful?", type="SCALE", order=1
    )
    opt_joy = Option.objects.create(question=perma_q, label="10 - Completely", numeric_value=10, order=10)

    # 3. Create a participant user who completed baseline
    from users.models import User
    user = User.objects.create_user(
        username="participant", email="p@example.com", password="password",
        group=test_group, has_completed_sociodemographic=True,
        onboarding_completed_at=timezone.now(),
    )

    # 4. Create completed response sets
    rs_socio = ResponseSet.objects.create(user=user, questionnaire=socio_q, status='COMPLETED')
    Response.objects.create(response_set=rs_socio, question=gender_q, selected_option=opt_male)

    rs_signup = ResponseSet.objects.create(user=user, questionnaire=psy_q, status='COMPLETED', milestone='SIGNUP')
    Response.objects.create(response_set=rs_signup, question=perma_q, selected_option=opt_joy)

    # 5. Trigger the export task
    task = ExportTask.objects.create(user=admin_user, filters={'group': 'All'})
    generate_longitudinal_export_csv(task.id)

    # 6. Verify task succeeded and file is saved
    task.refresh_from_db()
    assert task.status == 'SUCCESS'
    assert task.file is not None

    # Read and assert file content
    csv_content = task.file.read().decode('utf-8')
    import csv
    import io
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    # Check Headers
    headers = rows[0]
    assert 'ParticipantID' in headers
    assert 'Socio_Gender' in headers
    assert 'PERMA_A1_SIGNUP' in headers
    assert 'PERMA_A1_7_DAYS' in headers

    # Check Data Row
    data_row = rows[1]
    assert data_row[0] == str(user.user_id)
    assert data_row[1] == user.username
    assert data_row[2] == test_group.name
    # Socio gender answer
    assert "Male" in csv_content
    # PERMA joy answer (numeric value)
    assert "10" in csv_content





@pytest.mark.django_db
def test_generate_posttest_export_csv_task(admin_user, test_group):
    from admin_tools.tasks import generate_posttest_export_csv
    from questionnaires.models import Questionnaire, Question, Option, ResponseSet, Response

    # 1. Create a psychometric questionnaire and questions
    psy_q = Questionnaire.objects.create(
        title="Battery", assessment_type='PSYCHOMETRIC', is_active=True
    )
    perma_q = Question.objects.create(
        questionnaire=psy_q, content="[PERMA] Feel joyful?", type="SCALE", order=1
    )
    opt_joy = Option.objects.create(question=perma_q, label="10 - Completely", numeric_value=10, order=10)

    # 2. Create a participant user who completed SIGNUP milestone
    from users.models import User
    user = User.objects.create_user(
        username="posttest_participant", email="pp@example.com", password="password",
        group=test_group, has_completed_sociodemographic=True
    )

    # 3. Create completed response set for SIGNUP milestone
    rs_posttest = ResponseSet.objects.create(user=user, questionnaire=psy_q, status='COMPLETED', milestone='SIGNUP')
    Response.objects.create(response_set=rs_posttest, question=perma_q, selected_option=opt_joy)

    # 4. Trigger the export task
    task = ExportTask.objects.create(user=admin_user, filters={'group': 'All'})
    generate_posttest_export_csv(task.id)

    # 5. Verify task succeeded and file is saved
    task.refresh_from_db()
    assert task.status == 'SUCCESS'
    assert task.file is not None

    # Read and assert file content
    csv_content = task.file.read().decode('utf-8')
    import csv
    import io
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    # Check Headers
    headers = rows[0]
    assert 'ParticipantID' in headers
    assert 'PERMA_A1_SIGNUP' in headers

    # Check Data Row
    data_row = rows[1]
    assert data_row[0] == str(user.user_id)
    assert "10" in csv_content


@pytest.mark.django_db
def test_generate_t1_export_csv_task(admin_user, test_group):
    from admin_tools.tasks import generate_t1_export_csv
    from questionnaires.models import Questionnaire, Question, Option, ResponseSet, Response

    # 1. Create a psychometric questionnaire and questions
    psy_q = Questionnaire.objects.create(
        title="Battery", assessment_type='PSYCHOMETRIC', is_active=True
    )
    perma_q = Question.objects.create(
        questionnaire=psy_q, content="[PERMA] Feel joyful?", type="SCALE", order=1
    )
    opt_joy = Option.objects.create(question=perma_q, label="10 - Completely", numeric_value=10, order=10)

    # 2. Create a participant user who completed 7_DAYS milestone
    from users.models import User
    user = User.objects.create_user(
        username="t1_participant", email="t1p@example.com", password="password",
        group=test_group, has_completed_sociodemographic=True
    )

    # 3. Create completed response set for 7_DAYS milestone
    rs_t1 = ResponseSet.objects.create(user=user, questionnaire=psy_q, status='COMPLETED', milestone='7_DAYS')
    Response.objects.create(response_set=rs_t1, question=perma_q, selected_option=opt_joy)

    # 4. Trigger the export task
    task = ExportTask.objects.create(user=admin_user, filters={'group': 'All'})
    generate_t1_export_csv(task.id)

    # 5. Verify task succeeded and file is saved
    task.refresh_from_db()
    assert task.status == 'SUCCESS'
    assert task.file is not None

    # Read and assert file content
    csv_content = task.file.read().decode('utf-8')
    import csv
    import io
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    # Check Headers
    headers = rows[0]
    assert 'ParticipantID' in headers
    assert 'PERMA_A1_7_DAYS' in headers

    # Check Data Row
    data_row = rows[1]
    assert data_row[0] == str(user.user_id)
    assert "10" in csv_content
