import csv
import logging
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from .models import ExportTask
from .tasks import generate_posttest_export_csv, generate_longitudinal_export_csv, generate_t1_export_csv, generate_t2_export_csv, generate_t3_export_csv, generate_t4_export_csv
from .serializers import ExportTaskSerializer
from users.models import User
from activities.models import Submission

logger = logging.getLogger(__name__)

class ExportDataCSVView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="experiment_data_spss.csv"'

        writer = csv.writer(response, quoting=csv.QUOTE_ALL)
        # Header: ParticipantID, Username, Email, Group, RegDate, ActivityTitle, SubmissionContent, SubmissionDate
        writer.writerow(['ParticipantID', 'Username', 'Email', 'Group', 'RegistrationDate', 'ActivityTitle', 'SubmissionContent', 'SubmissionDate'])

        submissions = Submission.objects.all().select_related('user', 'user__group', 'activity')
        for sub in submissions:
            writer.writerow([
                sub.user.pk,
                sub.user.username,
                sub.user.email,
                sub.user.group.name if sub.user.group else 'None',
                sub.user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                sub.activity.title,
                sub.content.replace('\n', ' '), # SPSS friendly: no newlines in text fields
                sub.submission_date.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response

class ExportT0DataCSVView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            group_name = request.data.get('group', 'All')
            task = ExportTask.objects.create(
                user=request.user,
                filters={'group': group_name}
            )
            
            generate_posttest_export_csv.delay(task.id)
            
            return Response({
                'task_id': task.id,
                'status': task.status
            }, status=202)
        except Exception as e:
            logger.error(f"Failed to trigger T0 baseline export: {e}")
            return Response({"detail": "Failed to initiate export process."}, status=500)


class ExportT1DataCSVView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            group_name = request.data.get('group', 'All')
            task = ExportTask.objects.create(
                user=request.user,
                filters={'group': group_name}
            )
            
            generate_t1_export_csv.delay(task.id)
            
            return Response({
                'task_id': task.id,
                'status': task.status
            }, status=202)
        except Exception as e:
            logger.error(f"Failed to trigger T1 export: {e}")

class ExportT2DataCSVView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            group_name = request.data.get('group', 'All')
            task = ExportTask.objects.create(
                user=request.user,
                filters={'group': group_name}
            )
            generate_t2_export_csv.delay(task.id)
            return Response({
                'task_id': task.id,
                'status': task.status
            }, status=202)
        except Exception as e:
            logger.error(f"Failed to trigger T2 export: {e}")
            return Response({"detail": "Failed to initiate export process."}, status=500)


class ExportT3DataCSVView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            group_name = request.data.get('group', 'All')
            task = ExportTask.objects.create(
                user=request.user,
                filters={'group': group_name}
            )
            generate_t3_export_csv.delay(task.id)
            return Response({
                'task_id': task.id,
                'status': task.status
            }, status=202)
        except Exception as e:
            logger.error(f"Failed to trigger T3 export: {e}")
            return Response({"detail": "Failed to initiate export process."}, status=500)


class ExportT4DataCSVView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            group_name = request.data.get('group', 'All')
            task = ExportTask.objects.create(
                user=request.user,
                filters={'group': group_name}
            )
            generate_t4_export_csv.delay(task.id)
            return Response({
                'task_id': task.id,
                'status': task.status
            }, status=202)
        except Exception as e:
            logger.error(f"Failed to trigger T4 export: {e}")
            return Response({"detail": "Failed to initiate export process."}, status=500)


class ExportLongitudinalDataCSVView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            group_name = request.data.get('group', 'All')
            task = ExportTask.objects.create(
                user=request.user,
                filters={'group': group_name}
            )
            
            generate_longitudinal_export_csv.delay(task.id)
            
            return Response({
                'task_id': task.id,
                'status': task.status
            }, status=202)
        except Exception as e:
            logger.error(f"Failed to trigger longitudinal export: {e}")
            return Response({"detail": "Failed to initiate export process."}, status=500)

class ExportTaskStatusView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, task_id):
        try:
            task = ExportTask.objects.get(id=task_id, user=request.user)
            serializer = ExportTaskSerializer(task)
            return Response(serializer.data)
        except ExportTask.DoesNotExist:
            return Response({'error': 'Task not found'}, status=404)
        except Exception as e:
            logger.error(f"Failed to fetch task status for {task_id}: {e}")
            return Response({"detail": "Internal server error"}, status=500)

class AdminDashboardAnalyticsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        import datetime
        from django.utils import timezone
        from django.db.models import Count
        from django.db.models.functions import TruncDate
        from questionnaires.models import ResponseSet
        from phases.models import Phase

        now = timezone.now()
        local_now = timezone.localtime(now) if timezone.is_aware(now) else now
        seven_days_ago = now - datetime.timedelta(days=7)

        user_qs = User.objects.filter(is_superuser=False)
        total_participants = user_qs.count()

        # --- Single query for all submission/baseline counts ---
        completed_baselines = ResponseSet.objects.filter(status='COMPLETED').count()
        total_activities = Submission.objects.count()
        total_submissions = completed_baselines + total_activities

        # --- Active users: two flat queries + Python set union (no loop) ---
        active_baseline_ids = set(
            ResponseSet.objects.filter(status='COMPLETED', completed_at__gte=seven_days_ago)
            .values_list('user_id', flat=True)
        )
        active_activity_ids = set(
            Submission.objects.filter(submission_date__gte=seven_days_ago)
            .values_list('user_id', flat=True)
        )
        active_users = active_baseline_ids | active_activity_ids
        active_rate = round((len(active_users) / total_participants * 100), 1) if total_participants > 0 else 0

        # --- Phase Status ---
        today = local_now.date()
        current_phase = Phase.objects.filter(start_date__lte=today, end_date__gte=today).first()
        current_phase_name = current_phase.name if current_phase else "Pre-Launch"

        # --- Engagement Trend: SINGLE aggregated query instead of 7 separate ones ---
        day_start_7 = (local_now - datetime.timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)

        baseline_by_day = (
            ResponseSet.objects
            .filter(status='COMPLETED', completed_at__gte=day_start_7)
            .annotate(day=TruncDate('completed_at'))
            .values('day')
            .annotate(count=Count('id'))
        )
        activity_by_day = (
            Submission.objects
            .filter(submission_date__gte=day_start_7)
            .annotate(day=TruncDate('submission_date'))
            .values('day')
            .annotate(count=Count('id'))
        )

        # Merge into a dict keyed by date
        day_counts = {}
        for row in baseline_by_day:
            day_counts[row['day']] = day_counts.get(row['day'], 0) + row['count']
        for row in activity_by_day:
            day_counts[row['day']] = day_counts.get(row['day'], 0) + row['count']

        engagement_trend = []
        for i in range(6, -1, -1):
            d = (local_now - datetime.timedelta(days=i)).date()
            engagement_trend.append({
                'date': d.strftime('%a %d'),
                'count': day_counts.get(d, 0)
            })

        # --- Recent Participants: bulk count queries instead of per-user N+1 ---
        recent_users = list(user_qs.select_related('group').order_by('-created_at')[:8])
        recent_user_ids = [u.user_id for u in recent_users]

        # Bulk: baselines per user
        baseline_counts = dict(
            ResponseSet.objects
            .filter(user_id__in=recent_user_ids, status='COMPLETED')
            .values('user_id')
            .annotate(c=Count('id'))
            .values_list('user_id', 'c')
        )
        # Bulk: activity submissions per user
        activity_counts = dict(
            Submission.objects
            .filter(user_id__in=recent_user_ids)
            .values('user_id')
            .annotate(c=Count('id'))
            .values_list('user_id', 'c')
        )

        recent_participants = []
        for u in recent_users:
            b = baseline_counts.get(u.user_id, 0)
            a = activity_counts.get(u.user_id, 0)
            recent_participants.append({
                'id': u.user_id,
                'username': u.username,
                'group': u.group.name if u.group else 'Unassigned',
                'submissions_count': f"{b + a}/9",
                'status': 'Active' if u.user_id in active_users else 'Inactive'
            })

        return Response({
            'total_participants': total_participants,
            'total_submissions': total_submissions,
            'active_rate_percentage': active_rate,
            'current_phase_name': current_phase_name,
            'engagement_trend': engagement_trend,
            'recent_participants': recent_participants
        })

