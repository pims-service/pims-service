"""
One-time backfill: send PERMA baseline reports to users who completed T0
before this feature was deployed.

Usage:
    python manage.py send_missing_signup_reports
    python manage.py send_missing_signup_reports --dry-run
"""
from django.core.management.base import BaseCommand

from questionnaires.models import ResponseSet, PermaReportLog
from questionnaires.tasks import send_perma_snapshot_report_task


class Command(BaseCommand):
    help = 'Dispatch PERMA baseline reports for pre-feature T0 completions.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print who would receive a report without dispatching any tasks.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        already_sent = set(
            PermaReportLog.objects.filter(milestone='SIGNUP')
            .values_list('user_id', flat=True)
        )

        candidates = (
            ResponseSet.objects
            .filter(
                status='COMPLETED',
                milestone='SIGNUP',
                questionnaire__assessment_type='PSYCHOMETRIC',
            )
            .exclude(user_id__in=already_sent)
            .select_related('user')
        )

        count = candidates.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No missing SIGNUP reports found — nothing to do.'))
            return

        self.stdout.write(f'Found {count} participant(s) missing a baseline report.')

        for rs in candidates:
            label = f'{rs.user.username} <{rs.user.email}> (ResponseSet {rs.id})'
            if dry_run:
                self.stdout.write(f'  [dry-run] would send: {label}')
            else:
                send_perma_snapshot_report_task.delay(str(rs.id), 'SIGNUP')
                self.stdout.write(f'  dispatched: {label}')

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'Dry run complete — {count} task(s) NOT dispatched.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Done — {count} baseline report task(s) dispatched to Celery.'
            ))
