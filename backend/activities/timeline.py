from dataclasses import dataclass
from datetime import timedelta
from typing import Optional, Tuple

from django.utils import timezone

ACTIVITY_WAVES = (
    'PRE_T1',
    'PRE_T_1M',
    'PRE_T2',
    'PRE_T3',
    'PRE_T4',
)

ACTIVITY_WAVE_CHOICES = tuple((wave, wave.replace('_', ' ')) for wave in ACTIVITY_WAVES)

WAVE_LABELS = {
    'PRE_T1': 'pre Week 1 assessment',
    'PRE_T_1M': 'pre 1-month assessment',
    'PRE_T2': 'pre 3-month assessment',
    'PRE_T3': 'pre 6-month assessment',
    'PRE_T4': 'pre 1-year assessment',
}

MILESTONE_BY_WAVE = {
    'PRE_T1': '7_DAYS',
    'PRE_T_1M': '1_MONTH',
    'PRE_T2': '3_MONTHS',
    'PRE_T3': '6_MONTHS',
    'PRE_T4': '1_YEAR',
}

WAVE_PREREQUISITES = {
    'PRE_T_1M': '7_DAYS',
    'PRE_T2': '1_MONTH',
    'PRE_T3': '3_MONTHS',
    'PRE_T4': '6_MONTHS',
}

ASSESSMENT_OFFSETS = {
    'PRE_T1': 7,
    'PRE_T_1M': 23,
    'PRE_T2': 90,
    'PRE_T3': 180,
    'PRE_T4': 365,
}

BLOCK_LENGTH_DAYS = 7


@dataclass(frozen=True)
class ActivityState:
    wave: str
    day_in_block: int


def _local_date(dt):
    if dt is None:
        return None
    if timezone.is_aware(dt):
        return timezone.localtime(dt).date()
    return dt.date()


def get_t1_reference_date(user):
    """Reference datetime for T2/T3/T4 offsets (T1 completion or fallback)."""
    from questionnaires.models import ResponseSet

    t1_completed_at = user.posttest_completed_at
    if not t1_completed_at:
        t1_rs = ResponseSet.objects.filter(
            user=user, status='COMPLETED', milestone='7_DAYS'
        ).first()
        if t1_rs:
            t1_completed_at = t1_rs.completed_at

    if t1_completed_at:
        return t1_completed_at
    if user.onboarding_completed_at:
        return user.onboarding_completed_at + timedelta(days=7)
    return None


def _completed_milestones(user):
    from questionnaires.models import ResponseSet

    completed = set(
        ResponseSet.objects.filter(
            user=user,
            status='COMPLETED',
            milestone__isnull=False,
            questionnaire__assessment_type='PSYCHOMETRIC',
        ).values_list('milestone', flat=True)
    )
    if user.has_completed_posttest:
        completed.add('7_DAYS')
    return completed


def _wave_calendar_bounds(user, wave, t1_ref) -> Optional[Tuple]:
    """Return (block_start_date, assessment_due_date) for a wave, ignoring completion."""
    if wave == 'PRE_T1':
        if not user.onboarding_completed_at:
            return None
        block_start = _local_date(user.onboarding_completed_at)
        assessment_due = block_start + timedelta(days=ASSESSMENT_OFFSETS['PRE_T1'])
        return block_start, assessment_due

    if not t1_ref:
        return None

    ref_date = _local_date(t1_ref)
    assessment_due = ref_date + timedelta(days=ASSESSMENT_OFFSETS[wave])
    block_start = assessment_due - timedelta(days=BLOCK_LENGTH_DAYS)
    return block_start, assessment_due


def _wave_prerequisites_met(wave, completed):
    prereq = WAVE_PREREQUISITES.get(wave)
    return prereq is None or prereq in completed


def get_active_activity_state(user) -> Optional[ActivityState]:
    """
    Returns the active pre-assessment activity wave and day-in-block (1-7),
    or None when the user is between waves.
    """
    if getattr(user, 'is_disqualified', False):
        return None
    if not user.onboarding_completed_at:
        return None

    today = timezone.localdate()
    t1_ref = get_t1_reference_date(user)
    completed = _completed_milestones(user)

    for wave in ACTIVITY_WAVES:
        milestone = MILESTONE_BY_WAVE[wave]
        if milestone in completed:
            continue
        if not _wave_prerequisites_met(wave, completed):
            continue

        bounds = _wave_calendar_bounds(user, wave, t1_ref)
        if bounds is None:
            continue

        block_start, assessment_due = bounds
        if block_start <= today < assessment_due:
            day_in_block = (today - block_start).days + 1
            if 1 <= day_in_block <= BLOCK_LENGTH_DAYS:
                return ActivityState(wave=wave, day_in_block=day_in_block)

    return None


def get_waves_for_tier3_evaluation(user):
    """
    Yields activity waves whose 7-day block has ended and should be evaluated
    for the Tier 3 daily miss protocol.
    """
    if not user.onboarding_completed_at:
        return

    today = timezone.localdate()
    t1_ref = get_t1_reference_date(user)
    completed = _completed_milestones(user)

    for wave in ACTIVITY_WAVES:
        if not _wave_prerequisites_met(wave, completed):
            continue

        bounds = _wave_calendar_bounds(user, wave, t1_ref)
        if bounds is None:
            continue

        _, assessment_due = bounds
        if today >= assessment_due:
            yield wave
