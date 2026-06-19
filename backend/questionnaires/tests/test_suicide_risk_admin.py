import pytest
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

from questionnaires.models import Questionnaire, Question, Option, ResponseSet, Response
from questionnaires.safety_cache import CACHE_KEY, refresh_suicide_risk_admin_cache
from questionnaires.tasks import refresh_suicide_risk_admin_cache_task


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
def test_refresh_cache_stores_flagged_and_opt_in_cases(test_user, test_group):
    psy_q = Questionnaire.objects.create(
        title="Battery", assessment_type="PSYCHOMETRIC", is_active=True
    )
    q = Question.objects.create(
        questionnaire=psy_q, content="[PHQ-9] Test", type="SCALE", order=33
    )
    opt = Option.objects.create(question=q, label="2", numeric_value=2, order=2)

    rs_flagged_opt_in = ResponseSet.objects.create(
        user=test_user,
        questionnaire=psy_q,
        status="COMPLETED",
        milestone="SIGNUP",
        completed_at=timezone.now(),
        suicide_risk_triggered=True,
        suicide_risk_opt_in=True,
        scores={"PHQ9_TOTAL": 10, "SIDAS_TOTAL": 5},
    )
    Response.objects.create(response_set=rs_flagged_opt_in, question=q, selected_option=opt)

    other_user = test_user.__class__.objects.create_user(
        username="flagged_no_optin",
        email="noopt@example.com",
        password="password",
        group=test_group,
    )
    ResponseSet.objects.create(
        user=other_user,
        questionnaire=psy_q,
        status="COMPLETED",
        milestone="7_DAYS",
        completed_at=timezone.now(),
        suicide_risk_triggered=True,
        suicide_risk_opt_in=False,
    )

    payload = refresh_suicide_risk_admin_cache()

    assert payload["total_flagged"] == 2
    assert payload["opt_in_count"] == 1
    assert cache.get(CACHE_KEY) is not None

    cached = cache.get(CACHE_KEY)
    assert len(cached["opt_in_cases"]) == 1
    assert cached["opt_in_cases"][0]["username"] == test_user.username
    assert cached["opt_in_cases"][0]["email"] == test_user.email


@pytest.mark.django_db
def test_celery_task_refreshes_cache(test_user):
    psy_q = Questionnaire.objects.create(
        title="Battery", assessment_type="PSYCHOMETRIC", is_active=True
    )
    ResponseSet.objects.create(
        user=test_user,
        questionnaire=psy_q,
        status="COMPLETED",
        milestone="SIGNUP",
        completed_at=timezone.now(),
        suicide_risk_triggered=True,
        suicide_risk_opt_in=True,
    )

    result = refresh_suicide_risk_admin_cache_task()
    assert result["total_flagged"] == 1
    assert result["opt_in_count"] == 1


@pytest.mark.django_db
def test_admin_api_returns_opt_in_cases_by_default(admin_user, test_user):
    psy_q = Questionnaire.objects.create(
        title="Battery", assessment_type="PSYCHOMETRIC", is_active=True
    )
    ResponseSet.objects.create(
        user=test_user,
        questionnaire=psy_q,
        status="COMPLETED",
        milestone="SIGNUP",
        completed_at=timezone.now(),
        suicide_risk_triggered=True,
        suicide_risk_opt_in=True,
    )
    refresh_suicide_risk_admin_cache()

    client = APIClient()
    client.force_authenticate(user=admin_user)
    res = client.get("/api/questionnaires/admin/suicide-risk-follow-ups/")
    assert res.status_code == 200
    assert res.data["opt_in_count"] == 1
    assert len(res.data["cases"]) == 1
    assert res.data["cases"][0]["username"] == test_user.username


@pytest.mark.django_db
def test_admin_api_show_all_includes_declined_opt_in(admin_user, test_user, test_group):
    psy_q = Questionnaire.objects.create(
        title="Battery", assessment_type="PSYCHOMETRIC", is_active=True
    )
    ResponseSet.objects.create(
        user=test_user,
        questionnaire=psy_q,
        status="COMPLETED",
        milestone="SIGNUP",
        completed_at=timezone.now(),
        suicide_risk_triggered=True,
        suicide_risk_opt_in=True,
    )
    other = test_user.__class__.objects.create_user(
        username="declined", email="d@example.com", password="password", group=test_group
    )
    ResponseSet.objects.create(
        user=other,
        questionnaire=psy_q,
        status="COMPLETED",
        milestone="7_DAYS",
        completed_at=timezone.now(),
        suicide_risk_triggered=True,
        suicide_risk_opt_in=False,
    )
    refresh_suicide_risk_admin_cache()

    client = APIClient()
    client.force_authenticate(user=admin_user)
    res = client.get("/api/questionnaires/admin/suicide-risk-follow-ups/?show=all")
    assert res.status_code == 200
    assert res.data["total_flagged"] == 2
    assert len(res.data["cases"]) == 2


@pytest.mark.django_db
def test_admin_api_lazy_refresh_on_cache_miss(admin_user, test_user):
    psy_q = Questionnaire.objects.create(
        title="Battery", assessment_type="PSYCHOMETRIC", is_active=True
    )
    ResponseSet.objects.create(
        user=test_user,
        questionnaire=psy_q,
        status="COMPLETED",
        milestone="SIGNUP",
        completed_at=timezone.now(),
        suicide_risk_triggered=True,
        suicide_risk_opt_in=True,
    )

    client = APIClient()
    client.force_authenticate(user=admin_user)
    res = client.get("/api/questionnaires/admin/suicide-risk-follow-ups/")
    assert res.status_code == 200
    assert res.data["opt_in_count"] == 1
    assert cache.get(CACHE_KEY) is not None


@pytest.mark.django_db
def test_participant_cannot_access_admin_suicide_risk_api(test_user):
    client = APIClient()
    client.force_authenticate(user=test_user)
    res = client.get("/api/questionnaires/admin/suicide-risk-follow-ups/")
    assert res.status_code == 403


@pytest.mark.django_db
def test_admin_api_filters_by_pending_status_by_default(admin_user, test_user):
    psy_q = Questionnaire.objects.create(
        title="Battery", assessment_type="PSYCHOMETRIC", is_active=True
    )
    # Pending case (default)
    ResponseSet.objects.create(
        user=test_user,
        questionnaire=psy_q,
        status="COMPLETED",
        milestone="SIGNUP",
        completed_at=timezone.now(),
        suicide_risk_triggered=True,
        suicide_risk_opt_in=True,
        suicide_risk_status="PENDING",
    )
    # Resolved case
    other = test_user.__class__.objects.create_user(
        username="resolved_user", email="res@example.com", password="password"
    )
    ResponseSet.objects.create(
        user=other,
        questionnaire=psy_q,
        status="COMPLETED",
        milestone="7_DAYS",
        completed_at=timezone.now(),
        suicide_risk_triggered=True,
        suicide_risk_opt_in=True,
        suicide_risk_status="RESOLVED",
    )
    refresh_suicide_risk_admin_cache()

    client = APIClient()
    client.force_authenticate(user=admin_user)
    res = client.get("/api/questionnaires/admin/suicide-risk-follow-ups/")
    assert res.status_code == 200
    assert len(res.data["cases"]) == 1
    assert res.data["cases"][0]["username"] == test_user.username


@pytest.mark.django_db
def test_admin_api_filters_by_resolved_status(admin_user, test_user):
    psy_q = Questionnaire.objects.create(
        title="Battery", assessment_type="PSYCHOMETRIC", is_active=True
    )
    # Pending case
    ResponseSet.objects.create(
        user=test_user,
        questionnaire=psy_q,
        status="COMPLETED",
        milestone="SIGNUP",
        completed_at=timezone.now(),
        suicide_risk_triggered=True,
        suicide_risk_opt_in=True,
        suicide_risk_status="PENDING",
    )
    # Resolved case
    other = test_user.__class__.objects.create_user(
        username="resolved_user", email="res@example.com", password="password"
    )
    ResponseSet.objects.create(
        user=other,
        questionnaire=psy_q,
        status="COMPLETED",
        milestone="7_DAYS",
        completed_at=timezone.now(),
        suicide_risk_triggered=True,
        suicide_risk_opt_in=True,
        suicide_risk_status="RESOLVED",
    )
    refresh_suicide_risk_admin_cache()

    client = APIClient()
    client.force_authenticate(user=admin_user)
    res = client.get("/api/questionnaires/admin/suicide-risk-follow-ups/?status=RESOLVED")
    assert res.status_code == 200
    assert len(res.data["cases"]) == 1
    assert res.data["cases"][0]["username"] == "resolved_user"


@pytest.mark.django_db
def test_patch_updates_status_and_invalidates_cache(admin_user, test_user):
    psy_q = Questionnaire.objects.create(
        title="Battery", assessment_type="PSYCHOMETRIC", is_active=True
    )
    rs = ResponseSet.objects.create(
        user=test_user,
        questionnaire=psy_q,
        status="COMPLETED",
        milestone="SIGNUP",
        completed_at=timezone.now(),
        suicide_risk_triggered=True,
        suicide_risk_opt_in=True,
        suicide_risk_status="PENDING",
    )
    refresh_suicide_risk_admin_cache()

    client = APIClient()
    client.force_authenticate(user=admin_user)
    res = client.patch(
        f"/api/questionnaires/admin/suicide-risk-follow-ups/{rs.id}/",
        {"suicide_risk_status": "RESOLVED"},
    )
    assert res.status_code == 200
    assert res.data["suicide_risk_status"] == "RESOLVED"

    # Verify database was updated
    rs.refresh_from_db()
    assert rs.suicide_risk_status == "RESOLVED"

    # Verify cache was updated
    cached = cache.get(CACHE_KEY)
    assert cached["cases"][0]["suicide_risk_status"] == "RESOLVED"


@pytest.mark.django_db
def test_patch_denies_participants(test_user):
    psy_q = Questionnaire.objects.create(
        title="Battery", assessment_type="PSYCHOMETRIC", is_active=True
    )
    rs = ResponseSet.objects.create(
        user=test_user,
        questionnaire=psy_q,
        status="COMPLETED",
        milestone="SIGNUP",
        completed_at=timezone.now(),
        suicide_risk_triggered=True,
        suicide_risk_opt_in=True,
    )
    client = APIClient()
    client.force_authenticate(user=test_user)
    res = client.patch(
        f"/api/questionnaires/admin/suicide-risk-follow-ups/{rs.id}/",
        {"suicide_risk_status": "RESOLVED"},
    )
    assert res.status_code == 403
