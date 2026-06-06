import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.core.management import call_command
from django.utils import timezone
from django.core.cache import cache
from freezegun import freeze_time
from datetime import timedelta

from activities.models import Activity, Submission
from groups.models import Group
from users.models import User

@pytest.mark.django_db
def test_activity_list_current_phase(baseline_client, test_phase):
    Activity.objects.create(
        title="Test Activity",
        description="Desc",
        assigned_phase=test_phase,
        activity_type="paragraph"
    )
    url = reverse('activity_list')
    response = baseline_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1

@pytest.mark.django_db
def test_submission_create(baseline_client, baseline_user, test_phase):
    baseline_user.onboarding_completed_at = timezone.now()
    baseline_user.save()

    activity = Activity.objects.create(
        title="Test Submission",
        description="Desc",
        assigned_phase=test_phase,
        activity_type="paragraph",
        day_number=1,
    )
    url = reverse('submission_create')
    data = {
        "activity": activity.id,
        "content": "My daily entry."
    }
    response = baseline_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_seed_creates_7_day_activities_for_all_groups():
    """Verify the seed command creates activities for all 7 days for all active groups."""
    call_command('seed_daily_tasks')

    groups = Group.objects.filter(is_active=True)
    assert groups.count() >= 4  # At least the 4 core groups

    for group in groups:
        activities = Activity.objects.filter(group=group)
        assert activities.count() == 7, f"{group.name} has {activities.count()} activities, expected 7"
        day_numbers = set(activities.values_list('day_number', flat=True))
        assert day_numbers == {1, 2, 3, 4, 5, 6, 7}, f"{group.name} missing days: {day_numbers}"


@pytest.mark.django_db
def test_seed_includes_extra_groups():
    """Verify that groups beyond the original 4 also get activities with fallback prompt."""
    Group.objects.create(name="ExtraResearchGroup", is_active=True)
    call_command('seed_daily_tasks')

    extra_activities = Activity.objects.filter(group__name="ExtraResearchGroup")
    assert extra_activities.count() == 7
    # Should use fallback prompt, not be empty
    for act in extra_activities:
        assert len(act.description) > 10


@pytest.mark.django_db
def test_seed_is_idempotent():
    """Running seed twice should not create duplicates."""
    call_command('seed_daily_tasks')
    count1 = Activity.objects.count()

    call_command('seed_daily_tasks')
    count2 = Activity.objects.count()

    assert count1 == count2


@pytest.mark.django_db
def test_full_7_day_journey(test_phase):
    """Verify a participant can complete activities for all 7 days and get blocked on day 8."""
    group = Group.objects.create(name="JourneyGroup")
    phase = test_phase

    # Create activities for all 7 days
    for day in range(1, 8):
        Activity.objects.create(
            title=f"Day {day} Task",
            description=f"Prompt for day {day}",
            assigned_phase=phase,
            group=group,
            activity_type="paragraph",
            day_number=day
        )

    base_time = timezone.now()
    user = User.objects.create_user(
        username="journey_user", email="journey@test.com", password="pwd",
        group=group, has_completed_sociodemographic=True,
        onboarding_completed_at=base_time
    )

    client = APIClient()
    client.force_authenticate(user=user)

    for day in range(1, 8):
        with freeze_time(base_time + timedelta(days=day - 1)):
            cache.clear()

            # Should see the correct day's activity
            response = client.get(reverse('daily-activity-current'))
            assert response.status_code == status.HTTP_200_OK, f"Day {day}: {response.data}"
            assert response.data['current_day'] == day
            assert f"Day {day} Task" in response.data['title']

            activity_id = response.data['id']
            words_20 = "word " * 20
            submit_resp = client.post(
                reverse('daily-activity-submit'),
                {
                    "activity": activity_id,
                    "entry_1": words_20,
                    "entry_2": words_20,
                    "entry_3": words_20
                },
                format='json'
            )
            assert submit_resp.status_code == status.HTTP_201_CREATED, f"Day {day} submit: {submit_resp.data}"

    # Day 8: trial period should be complete
    with freeze_time(base_time + timedelta(days=7)):
        cache.clear()
        response = client.get(reverse('daily-activity-current'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get('detail') == 'No active activity period.'

