import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta
from freezegun import freeze_time
from django.core.cache import cache

from users.models import User, Role
from questionnaires.models import Questionnaire, Question, Option, ResponseSet

@pytest.fixture(autouse=True)
def clear_redis_cache():
    cache.clear()
    yield
    cache.clear()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def participant_role(db):
    return Role.objects.get_or_create(name='Participant')[0]

@pytest.fixture
def fresh_user(db, participant_role):
    return User.objects.create_user(
        username='fresh_user',
        email='fresh@test.com',
        password='password123',
        role=participant_role,
        has_completed_sociodemographic=False
    )

@pytest.fixture
def onboarded_user(db, participant_role):
    return User.objects.create_user(
        username='onboarded_user',
        email='onboarded@test.com',
        password='password123',
        role=participant_role,
        has_completed_sociodemographic=True,
        onboarding_completed_at=timezone.now()
    )

@pytest.fixture
def questionnaire(db):
    q = Questionnaire.objects.create(
        title='Psychometric Scale Battery',
        assessment_type='PSYCHOMETRIC',
        is_active=True
    )
    return q

@pytest.mark.django_db
class TestTimelineScheduler:
    def test_onboarding_user_due_signup(self, fresh_user):
        assert fresh_user.get_due_milestone == 'SIGNUP'

    def test_timeline_milestones_due_sequence(self, onboarded_user, questionnaire):
        base_time = timezone.now()
        onboarded_user.onboarding_completed_at = base_time
        onboarded_user.save()

        # Day 0: None is due
        cache.clear()
        assert onboarded_user.get_due_milestone is None

        # Day 5: None is due
        cache.clear()
        with freeze_time(base_time + timedelta(days=5)):
            assert onboarded_user.get_due_milestone is None

        # Day 6 (Experiment Day 7): None is due yet
        cache.clear()
        with freeze_time(base_time + timedelta(days=6)):
            assert onboarded_user.get_due_milestone is None

        # Day 7 (Experiment Day 8): 7_DAYS is due
        cache.clear()
        with freeze_time(base_time + timedelta(days=7)):
            assert onboarded_user.get_due_milestone == '7_DAYS'
            
            cache_key = f"user_{onboarded_user.id}_due_milestone"
            assert cache.get(cache_key) == '7_DAYS'

            # Submit 7_DAYS ResponseSet
            ResponseSet.objects.create(
                user=onboarded_user,
                questionnaire=questionnaire,
                status='COMPLETED',
                milestone='7_DAYS',
                completed_at=timezone.now()
            )
            cache.delete(cache_key)
            cache.clear()
            assert onboarded_user.get_due_milestone is None

        # Day 29: 1_MONTH is not due yet (offset is 23 days after T1 completion = Day 30)
        cache.clear()
        with freeze_time(base_time + timedelta(days=29)):
            assert onboarded_user.get_due_milestone is None

        # Day 30: 1_MONTH is due
        cache.clear()
        with freeze_time(base_time + timedelta(days=30)):
            assert onboarded_user.get_due_milestone == '1_MONTH'
            
            # Submit 1_MONTH completion
            ResponseSet.objects.create(
                user=onboarded_user,
                questionnaire=questionnaire,
                status='COMPLETED',
                milestone='1_MONTH',
                completed_at=timezone.now()
            )
            cache.delete(f"user_{onboarded_user.id}_due_milestone")
            cache.clear()
            assert onboarded_user.get_due_milestone is None

        # Day 96: 3_MONTHS is not due yet (T1 completion + 90 days = Day 97)
        cache.clear()
        with freeze_time(base_time + timedelta(days=96)):
            assert onboarded_user.get_due_milestone is None

        # Day 97: 3_MONTHS is due
        cache.clear()
        with freeze_time(base_time + timedelta(days=97)):
            assert onboarded_user.get_due_milestone == '3_MONTHS'
            
            # Submit 3_MONTHS completion
            ResponseSet.objects.create(
                user=onboarded_user,
                questionnaire=questionnaire,
                status='COMPLETED',
                milestone='3_MONTHS',
                completed_at=timezone.now()
            )
            cache.delete(f"user_{onboarded_user.id}_due_milestone")
            cache.clear()
            assert onboarded_user.get_due_milestone is None

        # Day 186: 6_MONTHS is not due
        cache.clear()
        with freeze_time(base_time + timedelta(days=186)):
            assert onboarded_user.get_due_milestone is None

        # Day 187: 6_MONTHS is due
        cache.clear()
        with freeze_time(base_time + timedelta(days=187)):
            assert onboarded_user.get_due_milestone == '6_MONTHS'
            
            # Submit 6_MONTHS completion
            ResponseSet.objects.create(
                user=onboarded_user,
                questionnaire=questionnaire,
                status='COMPLETED',
                milestone='6_MONTHS',
                completed_at=timezone.now()
            )
            cache.delete(f"user_{onboarded_user.id}_due_milestone")
            cache.clear()
            assert onboarded_user.get_due_milestone is None

        # Day 371: 1_YEAR is not due
        cache.clear()
        with freeze_time(base_time + timedelta(days=371)):
            assert onboarded_user.get_due_milestone is None

        # Day 372: 1_YEAR is due
        cache.clear()
        with freeze_time(base_time + timedelta(days=372)):
            assert onboarded_user.get_due_milestone == '1_YEAR'
            
            # Submit 1_YEAR completion
            ResponseSet.objects.create(
                user=onboarded_user,
                questionnaire=questionnaire,
                status='COMPLETED',
                milestone='1_YEAR',
                completed_at=timezone.now()
            )
            cache.delete(f"user_{onboarded_user.id}_due_milestone")
            cache.clear()
            assert onboarded_user.get_due_milestone is None

    def test_cache_invalidation_on_submission(self, api_client, onboarded_user, questionnaire):
        base_time = timezone.now()
        onboarded_user.onboarding_completed_at = base_time
        onboarded_user.save()

        with freeze_time(base_time + timedelta(days=7)):
            assert onboarded_user.get_due_milestone == '7_DAYS'
            cache_key = f"user_{onboarded_user.id}_due_milestone"
            assert cache.get(cache_key) == '7_DAYS'

            # Populate other cache keys
            cache.set(f"user_{onboarded_user.id}_activity_state", "some_state")
            cache.set(f"user_{onboarded_user.id}_exp_day", 7)

            # Submit via ResponseSetSubmitSerializer
            rs = ResponseSet.objects.create(
                user=onboarded_user,
                questionnaire=questionnaire,
                status='DRAFT',
                milestone='7_DAYS'
            )

            q = Question.objects.create(questionnaire=questionnaire, content='Test Question', type='SCALE', order=1)
            opt = Option.objects.create(question=q, label='Good', numeric_value=1, order=1)

            from questionnaires.serializers import ResponseSetSubmitSerializer
            serializer = ResponseSetSubmitSerializer(
                instance=rs,
                data={'responses_data': [{'question_id': str(q.id), 'selected_option_id': str(opt.id)}]},
                partial=True
            )
            assert serializer.is_valid(), serializer.errors
            serializer.save()

            # Verify cache cleared
            assert cache.get(cache_key) is None
            assert cache.get(f"user_{onboarded_user.id}_activity_state") is None
            assert cache.get(f"user_{onboarded_user.id}_exp_day") is None

    def test_due_milestone_api_view(self, api_client, onboarded_user):
        api_client.force_authenticate(user=onboarded_user)
        url = '/api/questionnaires/due/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['due_milestone'] is None

        base_time = onboarded_user.onboarding_completed_at
        cache.clear()
        with freeze_time(base_time + timedelta(days=7)):
            response = api_client.get(url)
            assert response.status_code == status.HTTP_200_OK
            assert response.data['due_milestone'] == '7_DAYS'

    def test_due_milestone_api_unauthenticated(self, api_client):
        url = '/api/questionnaires/due/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_milestone_availability_by_timeline_delta(authenticated_client, test_user):
    # Mock onboarding_completed_at to 97 days ago, and T1 completion to 90 days ago.
    test_user.has_completed_sociodemographic = True
    test_user.has_completed_posttest = True  # Complete the 7_DAYS milestone
    test_user.onboarding_completed_at = timezone.now() - timedelta(days=97)
    test_user.posttest_completed_at = timezone.now() - timedelta(days=90)
    test_user.save()

    # Clear cache to ensure clean test run
    cache.clear()

    # Assert that the API endpoint returns 3_MONTHS as the due milestone.
    url = '/api/questionnaires/due/'
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['due_milestone'] == '3_MONTHS'


@pytest.mark.django_db
def test_due_milestone_immediately_after_day7_submission(authenticated_client, test_user):
    from activities.models import Activity, Submission
    from phases.models import Phase

    test_user.has_completed_sociodemographic = True
    test_user.onboarding_completed_at = timezone.now()
    test_user.save()

    # Clear cache
    cache.clear()

    # Day 0: Nothing due yet
    url = '/api/questionnaires/due/'
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['due_milestone'] is None

    # Create dummy activity and submission for PRE_T1 day 7
    phase = Phase.objects.create(phase_number=1, name="Phase 1", start_date=timezone.now(), end_date=timezone.now() + timedelta(days=30))
    activity = Activity.objects.create(
        title="Day 7 Activity",
        description="Day 7",
        assigned_phase=phase,
        activity_type="task",
        day_number=7
    )
    
    # Submit Day 7
    Submission.objects.create(
        user=test_user,
        activity=activity,
        content="Entry info",
        activity_wave="PRE_T1",
        experiment_day=7
    )

    # Cache should be cleared by signal, get_due_milestone should return 7_DAYS immediately
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['due_milestone'] == '7_DAYS'

