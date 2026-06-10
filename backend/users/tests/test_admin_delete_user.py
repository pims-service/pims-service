import pytest
from django.urls import reverse
from rest_framework import status

from activities.models import Activity, Submission
from groups.models import Group
from phases.models import Phase
from questionnaires.models import Questionnaire, ResponseSet
from support.models import SupportTicket
from users.models import User, UserConsent


@pytest.fixture
def participant_with_data(db, test_group, test_phase):
    user = User.objects.create_user(
        username="delete_me",
        email="delete_me@example.com",
        password="password123",
        group=test_group,
        full_name="Delete Me",
    )
    UserConsent.objects.create(user=user, agreed=True, consent_version="1.0")

    activity = Activity.objects.create(
        title="Daily Task",
        description="Prompt",
        assigned_phase=test_phase,
        group=test_group,
        activity_type="paragraph",
        day_number=1,
    )
    Submission.objects.create(user=user, activity=activity, content="entry", experiment_day=1)

    questionnaire = Questionnaire.objects.create(title="Battery", assessment_type="PSYCHOMETRIC")
    ResponseSet.objects.create(
        user=user,
        questionnaire=questionnaire,
        status="COMPLETED",
        milestone="SIGNUP",
    )

    SupportTicket.objects.create(user=user, subject="Help", message="Need support", status="Open")
    return user


@pytest.mark.django_db
def test_admin_delete_user_requires_confirmation(admin_client, participant_with_data):
    url = reverse("admin_user_delete", kwargs={"pk": participant_with_data.pk})

    response = admin_client.post(url, {"confirmation": "wrong phrase"}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert User.objects.filter(pk=participant_with_data.pk).exists()


@pytest.mark.django_db
def test_admin_delete_user_success(admin_client, participant_with_data):
    url = reverse("admin_user_delete", kwargs={"pk": participant_with_data.pk})
    user_id = participant_with_data.pk

    response = admin_client.post(url, {"confirmation": "Confirm Delete"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert not User.objects.filter(pk=user_id).exists()
    assert Submission.objects.filter(user_id=user_id).count() == 0
    assert ResponseSet.objects.filter(user_id=user_id).count() == 0
    assert SupportTicket.objects.filter(user_id=user_id).count() == 0
    assert UserConsent.objects.filter(user_id=user_id).count() == 0


@pytest.mark.django_db
def test_admin_delete_user_forbidden_for_non_admin(authenticated_client, participant_with_data):
    url = reverse("admin_user_delete", kwargs={"pk": participant_with_data.pk})

    response = authenticated_client.post(url, {"confirmation": "Confirm Delete"}, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert User.objects.filter(pk=participant_with_data.pk).exists()


@pytest.mark.django_db
def test_admin_cannot_delete_self(admin_client, admin_user):
    url = reverse("admin_user_delete", kwargs={"pk": admin_user.pk})

    response = admin_client.post(url, {"confirmation": "Confirm Delete"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert User.objects.filter(pk=admin_user.pk).exists()


@pytest.mark.django_db
def test_admin_cannot_delete_superuser(admin_client, db):
    other_admin = User.objects.create_superuser(
        username="other_admin",
        email="other_admin@example.com",
        password="adminpassword",
    )
    url = reverse("admin_user_delete", kwargs={"pk": other_admin.pk})

    response = admin_client.post(url, {"confirmation": "Confirm Delete"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert User.objects.filter(pk=other_admin.pk).exists()
