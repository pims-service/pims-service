"""
Redis-backed cache for admin suicide-risk follow-up dashboard.
Refreshed automatically when a risk flag is raised or a participant opts in,
plus once daily by Celery. Admin API reads from cache without hitting the DB each request.
"""
from django.core.cache import cache
from django.utils import timezone

from .models import ResponseSet

CACHE_KEY = "admin:suicide_risk_flagged_users"
CACHE_TTL_SECONDS = 60 * 60 * 26  # slightly over 24h so daily beat never serves stale empty window

MILESTONE_LABELS = {
    "SIGNUP": "T0 (Signup)",
    "7_DAYS": "T1 (7 Days)",
    "1_MONTH": "T-First-Month (1 Month)",
    "3_MONTHS": "T2 (3 Months)",
    "6_MONTHS": "T3 (6 Months)",
    "1_YEAR": "T4 (1 Year)",
    "90_DAYS": "T2 (90 Days)",
}


def _serialize_case(response_set):
    user = response_set.user
    scores = response_set.scores or {}
    return {
        "response_set_id": str(response_set.id),
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.display_name,
        "whatsapp_number": user.whatsapp_number or "",
        "group_name": user.group.name if user.group else None,
        "milestone": response_set.milestone,
        "milestone_label": MILESTONE_LABELS.get(response_set.milestone, response_set.milestone or "—"),
        "completed_at": response_set.completed_at.isoformat() if response_set.completed_at else None,
        "suicide_risk_triggered": response_set.suicide_risk_triggered,
        "suicide_risk_opt_in": response_set.suicide_risk_opt_in,
        "phq9_total": scores.get("PHQ9_TOTAL"),
        "sidas_total": scores.get("SIDAS_TOTAL"),
    }


def fetch_flagged_cases_from_db():
    """Optimized query for all suicide-risk-flagged response sets (both draft and completed)."""
    return (
        ResponseSet.objects.filter(
            suicide_risk_triggered=True,
        )
        .select_related("user", "user__group")
        .only(
            "id",
            "milestone",
            "completed_at",
            "suicide_risk_triggered",
            "suicide_risk_opt_in",
            "scores",
            "user__user_id",
            "user__username",
            "user__email",
            "user__full_name",
            "user__whatsapp_number",
            "user__group__name",
        )
        .order_by("-completed_at")
    )


def build_cache_payload():
    cases = [_serialize_case(rs) for rs in fetch_flagged_cases_from_db()]
    opt_in_cases = [c for c in cases if c["suicide_risk_opt_in"] is True]
    return {
        "last_refreshed_at": timezone.now().isoformat(),
        "total_flagged": len(cases),
        "opt_in_count": len(opt_in_cases),
        "cases": cases,
        "opt_in_cases": opt_in_cases,
    }


def refresh_suicide_risk_admin_cache():
    """Query DB and write payload to Redis. Returns the payload."""
    payload = build_cache_payload()
    cache.set(CACHE_KEY, payload, timeout=CACHE_TTL_SECONDS)
    return payload


def get_suicide_risk_admin_cache(refresh_if_missing=True):
    """
    Read cached admin dashboard data.
    On cache miss, optionally refresh synchronously so the page works before the first beat run.
    """
    payload = cache.get(CACHE_KEY)
    if payload is None and refresh_if_missing:
        payload = refresh_suicide_risk_admin_cache()
    return payload
