import pytest
from django.urls import reverse
from rest_framework import status
from questionnaires.models import Questionnaire, Question, Option, ResponseSet


def _create_questionnaire(is_baseline=False):
    q = Questionnaire.objects.create(
        title="Test Questionnaire",
        is_baseline=is_baseline,
        is_active=True,
    )
    question = Question.objects.create(
        questionnaire=q,
        content="How are you?",
        type="CHOICE",
        order=1,
        required=True,
    )
    option = Option.objects.create(
        question=question,
        label="Good",
        numeric_value=1,
        order=1,
    )
    return q, question, option


@pytest.mark.django_db
def test_baseline_completion_sets_flag(authenticated_client, test_user):
    questionnaire, question, option = _create_questionnaire(is_baseline=True)
    response_set = ResponseSet.objects.create(
        user=test_user,
        questionnaire=questionnaire,
        status='DRAFT',
    )

    url = reverse('response_set_submit', kwargs={'pk': response_set.pk})
    payload = {
        "responses_data": [
            {"question_id": question.id, "selected_option_id": option.id}
        ]
    }
    response = authenticated_client.post(url, payload, format='json')
    assert response.status_code == status.HTTP_200_OK

    test_user.refresh_from_db()
    assert test_user.has_completed_baseline is True


@pytest.mark.django_db
def test_non_baseline_completion_does_not_set_flag(authenticated_client, test_user):
    questionnaire, question, option = _create_questionnaire(is_baseline=False)
    response_set = ResponseSet.objects.create(
        user=test_user,
        questionnaire=questionnaire,
        status='DRAFT',
    )

    url = reverse('response_set_submit', kwargs={'pk': response_set.pk})
    payload = {
        "responses_data": [
            {"question_id": question.id, "selected_option_id": option.id}
        ]
    }
    response = authenticated_client.post(url, payload, format='json')
    assert response.status_code == status.HTTP_200_OK

    test_user.refresh_from_db()
    assert test_user.has_completed_baseline is False


@pytest.mark.django_db
def test_incomplete_submission_not_allowed(authenticated_client, test_user):
    """
    A COMPLETED response_set cannot be re-submitted (get_queryset filters by DRAFT only).
    """
    questionnaire, question, option = _create_questionnaire(is_baseline=True)
    response_set = ResponseSet.objects.create(
        user=test_user,
        questionnaire=questionnaire,
        status='COMPLETED',
    )

    url = reverse('response_set_submit', kwargs={'pk': response_set.pk})
    payload = {
        "responses_data": [
            {"question_id": question.id, "selected_option_id": option.id}
        ]
    }
    response = authenticated_client.post(url, payload, format='json')
    assert response.status_code == status.HTTP_404_NOT_FOUND

    test_user.refresh_from_db()
    assert test_user.has_completed_baseline is False


@pytest.mark.django_db
def test_protected_activity_endpoint_rejects_incomplete_baseline(authenticated_client, test_user, test_phase):
    from activities.models import Activity
    Activity.objects.create(
        title="Protected Activity",
        description="Desc",
        assigned_phase=test_phase,
        activity_type="paragraph",
    )
    assert test_user.has_completed_baseline is False

    url = reverse('activity_list')
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_protected_phases_endpoint_rejects_incomplete_baseline(authenticated_client, test_user):
    assert test_user.has_completed_baseline is False

    url = reverse('phase_list')
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_profile_returns_has_completed_baseline(authenticated_client, test_user):
    url = reverse('profile')
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert 'has_completed_baseline' in response.data
    assert response.data['has_completed_baseline'] is False
