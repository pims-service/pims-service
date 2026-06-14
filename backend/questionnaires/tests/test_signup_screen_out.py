import pytest
from django.core import mail
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from notifications.models import Notification
from questionnaires.models import Questionnaire, Question, Option, ResponseSet

User = get_user_model()


@pytest.fixture
def fresh_user(db):
    return User.objects.create_user(
        username='screenoutuser',
        email='screenout@example.com',
        password='password123',
    )


@pytest.fixture
def fresh_client(fresh_user):
    client = APIClient()
    client.force_authenticate(fresh_user)
    return client


def _create_signup_battery_with_risk_trigger():
    battery = Questionnaire.objects.create(
        title='Screen-out Battery',
        assessment_type='PSYCHOMETRIC',
        is_active=True,
    )
    q_phq9 = Question.objects.create(
        questionnaire=battery,
        content='[PHQ-9] Thoughts that you would be better off dead, or of hurting yourself',
        type='SCALE',
        order=32,
    )
    opt_safe = Option.objects.create(question=q_phq9, label='0 - Not at all', numeric_value=0, order=0)
    opt_risk = Option.objects.create(question=q_phq9, label='2 - More than half the days', numeric_value=2, order=2)
    return battery, q_phq9, opt_safe, opt_risk


@pytest.mark.django_db(transaction=True)
def test_signup_risk_sends_screen_out_email_not_welcome(fresh_client, fresh_user, test_group):
    test_group.is_active = True
    test_group.save()

    battery, q_phq9, _, opt_risk = _create_signup_battery_with_risk_trigger()

    fresh_user.has_completed_sociodemographic = True
    fresh_user.group = test_group
    fresh_user.save()

    rs = ResponseSet.objects.create(
        user=fresh_user,
        questionnaire=battery,
        milestone='SIGNUP',
        status='DRAFT',
    )

    url = reverse('response_set_submit', kwargs={'pk': rs.pk})
    response = fresh_client.post(
        url,
        {'responses_data': [{'question_id': q_phq9.id, 'selected_option_id': opt_risk.id}]},
        format='json',
    )
    assert response.status_code == status.HTTP_200_OK

    fresh_user.refresh_from_db()
    assert fresh_user.is_disqualified is True
    assert 'Safety screener exclusion' in fresh_user.disqualification_reason
    assert fresh_user.onboarding_completed_at is not None

    assert len(mail.outbox) == 1
    screen_out = mail.outbox[0]
    assert 'Thank you for your interest' in screen_out.subject
    assert 'not the right fit for you at this time' in screen_out.alternatives[0][0]
    assert Notification.objects.filter(user=fresh_user, n_type='email').count() == 0


@pytest.mark.django_db(transaction=True)
def test_signup_draft_risk_does_not_send_participant_email(fresh_client, fresh_user, test_group):
    test_group.is_active = True
    test_group.save()

    battery, q_phq9, _, opt_risk = _create_signup_battery_with_risk_trigger()

    fresh_user.has_completed_sociodemographic = True
    fresh_user.group = test_group
    fresh_user.save()

    rs = ResponseSet.objects.create(
        user=fresh_user,
        questionnaire=battery,
        milestone='SIGNUP',
        status='DRAFT',
    )

    draft_url = reverse('response_set_save_draft', kwargs={'pk': rs.pk})
    response = fresh_client.post(
        draft_url,
        {'responses_data': [{'question_id': q_phq9.id, 'selected_option_id': opt_risk.id}]},
        format='json',
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(mail.outbox) == 0
    assert Notification.objects.filter(user=fresh_user, n_type='email').count() == 0

    rs.refresh_from_db()
    assert rs.suicide_risk_triggered is True
