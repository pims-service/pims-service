import logging
import io
import os
import base64

from celery import shared_task

logger = logging.getLogger(__name__)

NAVY = '#2E4E90'
GREY = '#7A7A7A'

MILESTONE_SUBJECT = {
    'SIGNUP':    'Your baseline wellbeing report / آپ کی بیس لائن فلاح رپورٹ',
    '3_MONTHS':  'Your month-3 wellbeing report / آپ کی تین ماہ فلاح رپورٹ',
    '1_YEAR':    'Your month-12 wellbeing report / آپ کی بارہ ماہ فلاح رپورٹ',
}

MILESTONE_FILENAME = {
    'SIGNUP':   'pims_baseline_report.pdf',
    '3_MONTHS': 'pims_month3_report.pdf',
    '1_YEAR':   'pims_month12_report.pdf',
}


def _build_bar_chart(scores):
    """
    Generate a single vertical bar chart in PERMA Profiler style.
    Three groups of bars separated by whitespace:
      Group 1 – Overall (1 bar, navy)
      Group 2 – P, E, R, M, A (5 bars, navy)
      Group 3 – H, Hap, N, Lon (H/Hap navy; N/Lon grey)
    Y-axis fixed 0–10. Score value printed above every bar.
    English-only labels on the chart — Urdu lives in the HTML legend
    (matplotlib cannot shape Arabic/Urdu script correctly).
    Returns a base64-encoded PNG string.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np

    def _score(key):
        try:
            return round(float(scores.get(key, 0.0)), 1)
        except (TypeError, ValueError):
            return 0.0

    # All bars in display order, with gaps between groups (None = gap slot)
    bars_def = [
        ('Overall', _score('PERMA_OVERALL'), NAVY),
        (None, None, None),
        ('P',   _score('PERMA_P'),   NAVY),
        ('E',   _score('PERMA_E'),   NAVY),
        ('R',   _score('PERMA_R'),   NAVY),
        ('M',   _score('PERMA_M'),   NAVY),
        ('A',   _score('PERMA_A'),   NAVY),
        (None, None, None),
        ('H',   _score('PERMA_H'),   NAVY),
        ('Hap', _score('PERMA_HAP'), NAVY),
        ('N',   _score('PERMA_N'),   GREY),
        ('Lon', _score('PERMA_LON'), GREY),
    ]

    labels = [b[0] if b[0] else '' for b in bars_def]
    vals   = [b[1] if b[1] is not None else 0.0 for b in bars_def]
    colors = [b[2] if b[2] else 'none' for b in bars_def]
    x      = np.arange(len(bars_def))

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)

    for i, (label, val, color) in enumerate(bars_def):
        if label is None:
            continue
        bar = ax.bar(i, val, color=color, width=0.6, edgecolor='none', zorder=3)
        # Value label above bar
        ax.text(i, val + 0.18, f'{val}', ha='center', va='bottom',
                color=color, fontsize=8.5, fontweight='bold')

    ax.set_ylim(0, 10)
    ax.set_xlim(-0.6, len(bars_def) - 0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10, color=NAVY, fontweight='bold')
    ax.set_ylabel('Score (0 – 10)', fontsize=8, color='#555555', labelpad=4)
    ax.yaxis.set_tick_params(labelsize=9, colors=NAVY)

    # Gridlines on y-axis only
    ax.yaxis.grid(True, linestyle='--', alpha=0.4, color='#cccccc', zorder=0)
    ax.set_axisbelow(True)

    # Clean spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color(NAVY)
    ax.tick_params(axis='x', bottom=False)

    # Group separator lines
    ax.axvline(x=1.5, color='#e0e0e0', linewidth=1, linestyle='-', zorder=1)
    ax.axvline(x=7.5, color='#e0e0e0', linewidth=1, linestyle='-', zorder=1)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor='white')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def _load_logo_base64():
    """Try common locations for the PIMS logo; return base64 string or empty string."""
    from django.conf import settings as djsettings
    candidates = [
        os.path.join(djsettings.BASE_DIR, 'static', 'pims_logo-removebg.png'),
        os.path.join(djsettings.BASE_DIR, 'static', 'pims_logo.png'),
        os.path.join(djsettings.BASE_DIR, 'pims_logo-removebg.png'),
        os.path.join(os.path.dirname(djsettings.BASE_DIR), 'pims_logo-removebg.png'),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    return base64.b64encode(f.read()).decode('utf-8')
            except OSError:
                continue
    return ''


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_perma_snapshot_report_task(self, response_set_id, milestone):
    """
    Generate and email a PERMA snapshot PDF report for a completed assessment.
    Spec: horizontal bar charts, 3 blocks, bilingual, mandatory support footer.
    Idempotent: will not send twice for the same user+milestone.
    """
    from django.conf import settings as djsettings
    from django.template.loader import render_to_string
    from weasyprint import HTML
    from questionnaires.models import ResponseSet, PermaReportLog
    from emails.tasks import _send_participant_email

    logger.info("PERMA report: starting for ResponseSet %s milestone=%s", response_set_id, milestone)

    try:
        response_set = ResponseSet.objects.select_related('user').get(id=response_set_id)
        user = response_set.user

        if not user.email:
            logger.error("PERMA report: user %s has no email. Skipping.", user.username)
            return {'status': 'skipped', 'reason': 'missing_email'}

        # ── Idempotency: skip if already sent ─────────────────────────────────
        if PermaReportLog.objects.filter(user=user, milestone=milestone).exists():
            logger.info("PERMA report: already sent for user %s milestone=%s. Skipping.", user.username, milestone)
            return {'status': 'skipped', 'reason': 'already_sent'}

        scores = response_set.scores or {}
        if not scores:
            logger.error("PERMA report: no scores on ResponseSet %s. Skipping.", response_set_id)
            PermaReportLog.objects.create(user=user, milestone=milestone, status='skipped',
                                          error_detail='No scores on ResponseSet.')
            return {'status': 'skipped', 'reason': 'no_scores'}

        # ── Build chart ───────────────────────────────────────────────────────
        chart_b64 = _build_bar_chart(scores)

        # ── Load logo ─────────────────────────────────────────────────────────
        logo_b64 = _load_logo_base64()

        # ── Font path for WeasyPrint ──────────────────────────────────────────
        font_path = os.path.join(djsettings.BASE_DIR, 'static', 'fonts', 'JameelNooriNastaleeq.ttf')

        # ── Milestone display label ───────────────────────────────────────────
        milestone_labels = {
            'SIGNUP':   ('Baseline', 'بیس لائن'),
            '3_MONTHS': ('Month 3',  'تین ماہ'),
            '1_YEAR':   ('Month 12', 'بارہ ماہ'),
        }
        label_en, label_ur = milestone_labels.get(milestone, (milestone, milestone))

        # ── Render HTML → PDF ─────────────────────────────────────────────────
        context = {
            'chart_image': chart_b64,
            'logo_image':  logo_b64,
            'font_path':   font_path,
            'label_en':    label_en,
            'label_ur':    label_ur,
        }
        html_string = render_to_string('questionnaires/perma_snapshot_report.html', context)
        pdf_bytes = HTML(string=html_string).write_pdf()

        # ── Send email ────────────────────────────────────────────────────────
        subject = MILESTONE_SUBJECT.get(milestone, 'Your wellbeing report')
        filename = MILESTONE_FILENAME.get(milestone, 'pims_report.pdf')

        _send_participant_email(
            {
                'subject': subject,
                'html_content': (
                    '<p>Dear Participant,</p>'
                    '<p>Please find your PERMA Profiler wellbeing report attached.</p>'
                    '<p dir="rtl" style="text-align:right;font-family:Arial,sans-serif;">'
                    'عزیز شریک،<br>براہ کرم منسلک PERMA پروفائلر فلاح رپورٹ دیکھیں۔</p>'
                    '<p>Thank you for your participation.</p>'
                    '<p dir="rtl" style="text-align:right;font-family:Arial,sans-serif;">'
                    'آپ کی شرکت کا شکریہ۔</p>'
                ),
                'text_content': (
                    'Dear Participant,\n\n'
                    'Please find your PERMA Profiler wellbeing report attached.\n\n'
                    'Thank you for your participation.'
                ),
            },
            user.email,
            attachments=[(filename, pdf_bytes, 'application/pdf')],
        )

        # ── Audit log ─────────────────────────────────────────────────────────
        PermaReportLog.objects.create(user=user, milestone=milestone, status='sent')
        logger.info("PERMA report: sent to %s for milestone=%s", user.email, milestone)
        return {'status': 'sent', 'recipient': user.email, 'milestone': milestone}

    except Exception as exc:
        logger.exception("PERMA report: failed for ResponseSet %s milestone=%s", response_set_id, milestone)
        try:
            from questionnaires.models import PermaReportLog, ResponseSet as RS
            rs = RS.objects.select_related('user').get(id=response_set_id)
            PermaReportLog.objects.update_or_create(
                user=rs.user, milestone=milestone,
                defaults={'status': 'error', 'error_detail': str(exc)},
            )
        except Exception:
            pass
        raise self.retry(exc=exc)


@shared_task
def check_and_send_perma_reports():
    """
    Daily cron: find COMPLETED PSYCHOMETRIC assessments for 3_MONTHS and 1_YEAR
    that have not yet had a report sent, and fire the report task for each.
    Acts as a catch-up safety net alongside the event-driven triggers in the serializer.
    """
    from questionnaires.models import ResponseSet, PermaReportLog

    report_milestones = ('3_MONTHS', '1_YEAR')
    qs = ResponseSet.objects.filter(
        status='COMPLETED',
        milestone__in=report_milestones,
        questionnaire__assessment_type='PSYCHOMETRIC',
    ).select_related('user')

    already_sent_pairs = set(
        PermaReportLog.objects.filter(milestone__in=report_milestones)
        .values_list('user_id', 'milestone')
    )

    dispatched = 0
    for rs in qs:
        if (rs.user_id, rs.milestone) not in already_sent_pairs:
            send_perma_snapshot_report_task.delay(str(rs.id), rs.milestone)
            dispatched += 1

    logger.info("PERMA report cron: dispatched %d report tasks.", dispatched)
    return {'dispatched': dispatched}


@shared_task
def refresh_suicide_risk_admin_cache_task():
    """Daily Celery job: fetch flagged users from DB and store in Redis."""
    from .safety_cache import refresh_suicide_risk_admin_cache

    payload = refresh_suicide_risk_admin_cache()
    logger.info(
        "Suicide risk admin cache refreshed: %s flagged, %s opted in for follow-up.",
        payload["total_flagged"],
        payload["opt_in_count"],
    )
    return {
        "total_flagged": payload["total_flagged"],
        "opt_in_count": payload["opt_in_count"],
        "last_refreshed_at": payload["last_refreshed_at"],
    }
