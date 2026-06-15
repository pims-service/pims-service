import csv
import io
import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from admin_tools.models import ExportTask
from admin_tools.tasks import generate_daily_entries_export_csv, generate_t1_export_csv
from activities.models import Activity, Submission
from phases.models import Phase

User = get_user_model()

@pytest.mark.django_db
def test_daily_entries_export_flow(admin_user, test_group, test_phase):
    # Create Activity
    activity = Activity.objects.create(
        title="Day 1 Reflection",
        description="Write reflections",
        assigned_phase=test_phase,
        activity_type="paragraph",
        day_number=1,
    )
    
    # Create User
    user = User.objects.create_user(
        username="daily_participant",
        email="participant@example.com",
        password="password",
        group=test_group,
    )
    
    # Create Submission
    sub = Submission.objects.create(
        user=user,
        activity=activity,
        entry_1="This is a test entry number 1 that must exceed minimum length requirements.",
        entry_2="This is a test entry number 2 that must exceed minimum length requirements.",
        entry_3="This is a test entry number 3 that must exceed minimum length requirements.",
        activity_wave="PRE_T1",
        experiment_day=1,
        entry_1_focus_ts=timezone.now(),
        entry_2_focus_ts=timezone.now(),
        entry_3_focus_ts=timezone.now(),
        entry_1_submit_ts=timezone.now(),
        entry_2_submit_ts=timezone.now(),
        entry_3_submit_ts=timezone.now(),
        entry_1_duration_sec=30,
        entry_2_duration_sec=45,
        entry_3_duration_sec=60,
    )
    
    # Trigger generate_daily_entries_export_csv
    task = ExportTask.objects.create(user=admin_user, filters={"group": "All"})
    generate_daily_entries_export_csv(task.id)
    
    task.refresh_from_db()
    assert task.status == "SUCCESS"
    
    csv_content = task.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)
    
    # There should be 3 rows (one per non-empty entry)
    assert len(rows) == 3
    
    # Verify values
    for i, row in enumerate(rows, 1):
        assert row["participant_id"] == str(user.user_id)
        assert row["group_id"] == test_group.name
        assert row["window_id"] == "PRE_T1"
        assert row["day_number"] == "1"
        assert row["entry_number"] == str(i)
        assert row["day_total_words"] == "39" # 13 words * 3 entries
        assert row["day_entries_completed"] == "3"
        assert row["day_mean_words_per_entry"] == "13.0"
        
        if i == 1:
            assert row["entry_duration_sec"] == "30"
        elif i == 2:
            assert row["entry_duration_sec"] == "45"
        elif i == 3:
            assert row["entry_duration_sec"] == "60"

@pytest.mark.django_db
def test_t1_export_includes_window_stats(admin_user, test_group, test_phase):
    # Setup questionnaire and needed objects to run generate_t1_export_csv
    from questionnaires.models import Questionnaire, ResponseSet
    
    psy_q = Questionnaire.objects.create(
        title="T1 Battery", assessment_type="PSYCHOMETRIC", is_active=True
    )
    
    user = User.objects.create_user(
        username="t1_window_user",
        email="t1_window@example.com",
        password="password",
        group=test_group,
    )
    
    activity = Activity.objects.create(
        title="Day 1 Reflection",
        description="Write reflections",
        assigned_phase=test_phase,
        activity_type="paragraph",
        day_number=1,
    )
    
    # 1 completed submission
    Submission.objects.create(
        user=user,
        activity=activity,
        entry_1="Entry one details go here.",
        entry_2="Entry two details go here.",
        entry_3="Entry three details go here.",
        activity_wave="PRE_T1",
        experiment_day=1,
        entry_1_duration_sec=10,
        entry_2_duration_sec=20,
        entry_3_duration_sec=30,
    )
    
    # Response set for completing T1 (7_DAYS milestone)
    ResponseSet.objects.create(
        user=user,
        questionnaire=psy_q,
        status="COMPLETED",
        milestone="7_DAYS",
    )
    
    task = ExportTask.objects.create(user=admin_user, filters={"group": "All"})
    generate_t1_export_csv(task.id)
    
    task.refresh_from_db()
    assert task.status == "SUCCESS"
    
    csv_content = task.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)
    
    assert len(rows) == 1
    row = rows[0]
    
    assert "window_mean_words_per_entry" in row
    assert "window_entries_completed" in row
    assert "window_days_completed" in row
    assert "window_total_words" in row
    assert "window_mean_session_duration_sec" in row
    
    assert row["window_entries_completed"] == "3"
    assert row["window_days_completed"] == "1"
    assert row["window_total_words"] == "15" # 5 words * 3 entries
    assert row["window_mean_session_duration_sec"] == "60.0"
