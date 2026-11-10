import pytest
from django.core import mail
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from groups.models import Group
from groups.services import free_group_places, try_assign_user_to_group
from groups.tasks import assign_unassigned_participants
from questionnaires.models import Questionnaire, Question, Option, ResponseSet
from users.models import User


def _make_user(username, **extra):
    return User.objects.create_user(username=username, email=f"{username}@example.com", password="pass1234", **extra)


def _full_group():
    group = Group.objects.create(name="Cap_Full", description="", is_active=True, capacity=1)
    _make_user("cap_member", group=group)
    return group


@pytest.mark.django_db(transaction=True)
def test_try_assign_returns_none_and_alerts_once_when_full():
    Group.objects.all().delete()
    _full_group()
    u1, u2 = _make_user("cap_u1"), _make_user("cap_u2")

    assert try_assign_user_to_group(u1) is None
    assert try_assign_user_to_group(u2) is None
    u1.refresh_from_db()
    assert u1.group is None
    # Throttled: one alert for repeated failures.
    alerts = [m for m in mail.outbox if 'Study groups almost full' in m.subject]
    assert len(alerts) == 1


@pytest.mark.django_db
def test_free_group_places_ignores_inactive_and_overfull():
    Group.objects.all().delete()
    Group.objects.create(name="Cap_A", description="", is_active=True, capacity=3)
    Group.objects.create(name="Cap_Inactive", description="", is_active=False, capacity=50)
    over = Group.objects.create(name="Cap_Over", description="", is_active=True, capacity=1)
    _make_user("cap_o1", group=over)
    _make_user("cap_o2", group=over)
    assert free_group_places() == 3


@pytest.mark.django_db
def test_assign_unassigned_participants_assigns_eligible_only():
    Group.objects.all().delete()
    group = Group.objects.create(name="Cap_Open", description="", is_active=True, capacity=50)
    waiting = _make_user("cap_wait", has_completed_sociodemographic=True)
    disq = _make_user("cap_disq", has_completed_sociodemographic=True, is_disqualified=True)
    not_screened = _make_user("cap_new")

    result = assign_unassigned_participants()

    assert result == {'assigned': 1, 'still_waiting': 0}
    waiting.refresh_from_db(); disq.refresh_from_db(); not_screened.refresh_from_db()
    assert waiting.group == group
    assert disq.group is None
    assert not_screened.group is None


@pytest.mark.django_db(transaction=True)
def test_screener_submit_succeeds_when_all_groups_full():
    Group.objects.all().delete()
    _full_group()
    user = _make_user("cap_socio")
    client = APIClient()
    client.force_authenticate(user)

    socio = Questionnaire.objects.create(title="Socio Form", assessment_type='SOCIODEMOGRAPHIC', is_active=True)
    q = Question.objects.create(questionnaire=socio, content="Gender?", type="CHOICE", order=1)
    opt = Option.objects.create(question=q, label="Male", numeric_value=1, order=1)
    rs = ResponseSet.objects.create(user=user, questionnaire=socio, status='DRAFT')

    response = client.post(
        reverse('response_set_submit', kwargs={'pk': rs.pk}),
        {"responses_data": [{"question_id": q.id, "selected_option_id": opt.id}]},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db(); rs.refresh_from_db()
    assert rs.status == 'COMPLETED'
    assert user.has_completed_sociodemographic is True
    assert user.group is None
