import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from groups.models import Group
from questionnaires.models import Questionnaire, Question, Option, ResponseSet
from users.models import User


def _questionnaire(assessment_type):
    q = Questionnaire.objects.create(title=f"MS {assessment_type}", assessment_type=assessment_type, is_active=True)
    question = Question.objects.create(questionnaire=q, content="Q?", type="CHOICE", order=1)
    option = Option.objects.create(question=question, label="A", numeric_value=1, order=1)
    return q, question, option


def _submit(client, rs, question, option):
    return client.post(
        reverse('response_set_submit', kwargs={'pk': rs.pk}),
        {"responses_data": [{"question_id": question.id, "selected_option_id": option.id}]},
        format='json',
    )


@pytest.mark.django_db(transaction=True)
def test_first_active_submission_flag_is_stable_on_retry():
    group = Group.objects.create(name="MS_Group", description="", is_active=True, capacity=50)
    user = User.objects.create_user(
        username="ms_user", email="ms@example.com", password="pass1234",
        group=group, has_completed_sociodemographic=True,
    )
    client = APIClient()
    client.force_authenticate(user)

    socio, sq, so = _questionnaire('SOCIODEMOGRAPHIC')
    rs_socio = ResponseSet.objects.create(user=user, questionnaire=socio, status='DRAFT')
    res = _submit(client, rs_socio, sq, so)
    assert res.status_code == 200
    assert res.data['first_active_submission'] is False
    assert res.data['eligible_signup'] is True
    assert res.data['completed_7day'] is False
    # Retry of the screener: still reported, so the client can fire it if the first reply was lost.
    assert _submit(client, rs_socio, sq, so).data['eligible_signup'] is True

    battery, bq, bo = _questionnaire('PSYCHOMETRIC')
    rs = ResponseSet.objects.create(user=user, questionnaire=battery, milestone='SIGNUP', status='DRAFT')
    first = _submit(client, rs, bq, bo)
    assert first.status_code == 200
    assert first.data['first_active_submission'] is True
    assert first.data['eligible_signup'] is False
    assert first.data['user_id'] == user.pk

    # Retry of the same (already completed) set: same answer, so a lost reply is not a lost event.
    retry = _submit(client, rs, bq, bo)
    assert retry.status_code == 200
    assert retry.data['first_active_submission'] is True

    rs_d7 = ResponseSet.objects.create(user=user, questionnaire=battery, milestone='7_DAYS', status='DRAFT')
    d7 = _submit(client, rs_d7, bq, bo)
    assert d7.status_code == 200
    assert d7.data['completed_7day'] is True
    assert d7.data['first_active_submission'] is False


@pytest.mark.django_db(transaction=True)
def test_disqualified_screener_is_not_an_eligible_signup():
    user = User.objects.create_user(username="ms_disq", email="ms_disq@example.com", password="pass1234")
    client = APIClient()
    client.force_authenticate(user)
    socio = Questionnaire.objects.create(title="MS Socio DQ", assessment_type='SOCIODEMOGRAPHIC', is_active=True)
    q = Question.objects.create(questionnaire=socio, content="Eligible?", type="CHOICE", order=1)
    opt = Option.objects.create(question=q, label="No - DISQUALIFY", numeric_value=0, order=1)
    rs = ResponseSet.objects.create(user=user, questionnaire=socio, status='DRAFT')
    res = _submit(client, rs, q, opt)
    assert res.status_code == 200
    assert res.data['eligible_signup'] is False
