import pytest
from django.urls import reverse
from rest_framework import status

from activities.models import Activity, Submission
from users.models import User


@pytest.mark.django_db
def test_self_delete_requires_username_confirmation(authenticated_client, test_user, test_phase):
    activity = Activity.objects.create(
        title="Daily Task",
        description="Prompt",
        assigned_phase=test_phase,
        activity_type="paragraph",
        day_number=1,
    )
    Submission.objects.create(user=test_user, activity=activity, content="entry", experiment_day=1)

    url = reverse("account_self_delete")
    response = authenticated_client.post(
        url,
        {"confirmation": "Confirm Delete", "password": "password123"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert User.objects.filter(pk=test_user.pk).exists()


@pytest.mark.django_db
def test_self_delete_success(authenticated_client, test_user):
    username = test_user.username
    user_id = test_user.pk
    url = reverse("account_self_delete")

    response = authenticated_client.post(
        url,
        {"confirmation": f"{username} Confirm Delete", "password": "password123"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert not User.objects.filter(pk=user_id).exists()
    assert Submission.objects.filter(user_id=user_id).count() == 0


@pytest.mark.django_db
def test_self_delete_forbidden_for_superuser(admin_client, admin_user):
    url = reverse("account_self_delete")
    response = admin_client.post(
        url,
        {
            "confirmation": f"{admin_user.username} Confirm Delete",
            "password": "adminpassword",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert User.objects.filter(pk=admin_user.pk).exists()


@pytest.mark.django_db
def test_self_delete_rejects_incorrect_password(authenticated_client, test_user):
    url = reverse("account_self_delete")
    response = authenticated_client.post(
        url,
        {
            "confirmation": f"{test_user.username} Confirm Delete",
            "password": "wrong-password",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Incorrect password" in response.data["detail"]
    assert User.objects.filter(pk=test_user.pk).exists()


@pytest.mark.django_db
def test_self_delete_requires_authentication(api_client, test_user):
    url = reverse("account_self_delete")
    response = api_client.post(
        url,
        {"confirmation": f"{test_user.username} Confirm Delete"},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert User.objects.filter(pk=test_user.pk).exists()
