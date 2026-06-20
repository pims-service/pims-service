import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.core import mail
from questionnaires.models import Questionnaire, Question, Option, ResponseSet
from groups.models import Group

User = get_user_model()

@pytest.fixture
def fresh_user(db):
    return User.objects.create_user(
        username="freshuser",
        email="fresh@example.com",
        password="password123"
    )

@pytest.fixture
def fresh_client(fresh_user):
    client = APIClient()
    client.force_authenticate(fresh_user)
    return client

def _create_test_scales():
    # 1. Socio form
    socio = Questionnaire.objects.create(
        title="Socio Form",
        assessment_type='SOCIODEMOGRAPHIC',
        is_active=True
    )
    q_socio = Question.objects.create(questionnaire=socio, content="Gender?", type="CHOICE", order=1)
    opt_socio = Option.objects.create(question=q_socio, label="Male", numeric_value=1, order=1)

    # 2. Psychometric Scales (SIGNUP milestone)
    battery = Questionnaire.objects.create(
        title="Scales Battery",
        assessment_type='PSYCHOMETRIC',
        is_active=True
    )
    q_battery = Question.objects.create(questionnaire=battery, content="Joyful?", type="SCALE", order=1)
    opt_battery = Option.objects.create(question=q_battery, label="10", numeric_value=10, order=10)

    return socio, q_socio, opt_socio, battery, q_battery, opt_battery

@pytest.mark.django_db
def test_user_onboarding_default_state(fresh_user):
    """Verify newly created users have onboarding flags set to False and no group assigned."""
    assert fresh_user.has_completed_sociodemographic is False
    assert fresh_user.has_completed_sociodemographic is False
    assert fresh_user.group is None

@pytest.mark.django_db(transaction=True)
def test_sociodemographic_submission_completes_onboarding(fresh_client, fresh_user, test_group):
    """
    Submitting the sociodemographic questionnaire completed sociodemographic status,
    and then submitting the baseline psychometrics completes onboarding, setting onboarding_completed_at.
    """
    # Ensure there is an active group in database
    test_group.is_active = True
    test_group.save()

    socio, q_socio, opt_socio, battery, q_battery, opt_battery = _create_test_scales()

    # 1. Create and submit response set for socio
    rs = ResponseSet.objects.create(
        user=fresh_user,
        questionnaire=socio,
        status='DRAFT'
    )

    url = reverse('response_set_submit', kwargs={'pk': rs.pk})
    payload = {
        "responses_data": [
            {"question_id": q_socio.id, "selected_option_id": opt_socio.id}
        ]
    }
    
    response = fresh_client.post(url, payload, format='json')
    assert response.status_code == status.HTTP_200_OK

    fresh_user.refresh_from_db()
    assert fresh_user.has_completed_sociodemographic is True
    assert fresh_user.onboarding_completed_at is None  # Onboarding is NOT complete yet
    assert fresh_user.group is not None  # Assigned to group immediately
    assert fresh_user.group.is_active is True

    # 2. Create and submit baseline psychometrics (SIGNUP milestone)
    rs_battery = ResponseSet.objects.create(
        user=fresh_user,
        questionnaire=battery,
        milestone='SIGNUP',
        status='DRAFT'
    )

    url_battery = reverse('response_set_submit', kwargs={'pk': rs_battery.pk})
    payload_battery = {
        "responses_data": [
            {"question_id": q_battery.id, "selected_option_id": opt_battery.id}
        ]
    }

    response2 = fresh_client.post(url_battery, payload_battery, format='json')
    assert response2.status_code == status.HTTP_200_OK

    fresh_user.refresh_from_db()
    assert fresh_user.onboarding_completed_at is not None  # Now onboarding is fully complete
    # Welcome email + PERMA baseline report email are both sent on SIGNUP completion
    assert len(mail.outbox) == 2
    subjects = [m.subject for m in mail.outbox]
    assert any('Welcome to Psycheversity' in s for s in subjects)
    welcome = next(m for m in mail.outbox if 'Welcome to Psycheversity' in m.subject)
    assert 'سائیکیورسٹی میں خوش آمدید' in welcome.subject
    assert welcome.to == [fresh_user.email]

@pytest.mark.django_db(transaction=True)
def test_sociodemographic_disqualification(fresh_client, fresh_user, test_group):
    """
    Submitting a sociodemographic response set with a disqualifying answer
    marks the user as disqualified and does NOT assign a group or complete onboarding.
    """
    test_group.is_active = True
    test_group.save()

    # Create socio form
    socio = Questionnaire.objects.create(
        title="Socio Form",
        assessment_type='SOCIODEMOGRAPHIC',
        is_active=True
    )
    q_socio = Question.objects.create(questionnaire=socio, content="Are you eligible?", type="CHOICE", order=1)
    # A label containing DISQUALIFY
    opt_disqualify = Option.objects.create(question=q_socio, label="No (DISQUALIFY)", numeric_value=0, order=1)

    rs = ResponseSet.objects.create(
        user=fresh_user,
        questionnaire=socio,
        milestone='SIGNUP',
        status='DRAFT'
    )

    url = reverse('response_set_submit', kwargs={'pk': rs.pk})
    payload = {
        "responses_data": [
            {"question_id": q_socio.id, "selected_option_id": opt_disqualify.id}
        ]
    }
    
    response = fresh_client.post(url, payload, format='json')
    assert response.status_code == status.HTTP_200_OK

    fresh_user.refresh_from_db()
    assert fresh_user.is_disqualified is True
    assert fresh_user.disqualification_reason != ""
    assert fresh_user.has_completed_sociodemographic is False
    assert fresh_user.group is None
    assert len(mail.outbox) == 1
    disqualification = mail.outbox[0]
    assert 'Thank you for your interest' in disqualification.subject
    assert 'not the right fit for you at this time' in disqualification.alternatives[0][0]

@pytest.mark.django_db(transaction=True)
def test_sociodemographic_disqualification_by_order(fresh_client, fresh_user, test_group):
    """
    Submitting a sociodemographic response set with a question of order 11/12
    having option of numeric_value=1 (e.g. Yes) marks user as disqualified.
    """
    test_group.is_active = True
    test_group.save()

    # Create socio form
    socio = Questionnaire.objects.create(
        title="Socio Form",
        assessment_type='SOCIODEMOGRAPHIC',
        is_active=True
    )
    # Question with order 11
    q_socio = Question.objects.create(questionnaire=socio, content="Taking medication?", type="CHOICE", order=11)
    opt_yes = Option.objects.create(question=q_socio, label="Yes", numeric_value=1, order=1)

    rs = ResponseSet.objects.create(
        user=fresh_user,
        questionnaire=socio,
        milestone='SIGNUP',
        status='DRAFT'
    )

    url = reverse('response_set_submit', kwargs={'pk': rs.pk})
    payload = {
        "responses_data": [
            {"question_id": q_socio.id, "selected_option_id": opt_yes.id}
        ]
    }
    
    response = fresh_client.post(url, payload, format='json')
    assert response.status_code == status.HTTP_200_OK

    fresh_user.refresh_from_db()
    assert fresh_user.is_disqualified is True
    assert fresh_user.disqualification_reason != ""
    assert fresh_user.has_completed_sociodemographic is False
    assert fresh_user.group is None
    assert len(mail.outbox) == 1

@pytest.mark.django_db
def test_7_days_milestone_completion_marks_posttest(fresh_client, fresh_user):
    """
    Submitting the psychometric battery for the 7_DAYS milestone
    sets the has_completed_posttest flag.
    """
    _, _, _, battery, q_battery, opt_battery = _create_test_scales()

    # Create response set for 7_DAYS
    rs = ResponseSet.objects.create(
        user=fresh_user,
        questionnaire=battery,
        milestone='7_DAYS',
        status='DRAFT'
    )

    url = reverse('response_set_submit', kwargs={'pk': rs.pk})
    payload = {
        "responses_data": [
            {"question_id": q_battery.id, "selected_option_id": opt_battery.id}
        ]
    }

    response = fresh_client.post(url, payload, format='json')
    assert response.status_code == status.HTTP_200_OK

    fresh_user.refresh_from_db()
    assert fresh_user.has_completed_posttest is True
    assert fresh_user.posttest_completed_at is not None
