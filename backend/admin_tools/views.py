import csv
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from users.models import User
from activities.models import Submission

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

class ExportBaselineDataCSVView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from questionnaires.models import ResponseSet
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="baseline_experiment_data_spss.csv"'

        writer = csv.writer(response, quoting=csv.QUOTE_ALL)
        
        # Get ordered questions for the baseline questionnaire to act as columns
        from questionnaires.models import Question
        questions = list(Question.objects.filter(questionnaire__is_baseline=True).order_by('order'))

        # Header for Wide Format (SPSS/Excel Compatible, no redundancy)
        static_headers = ['ParticipantID', 'Username', 'Group', 'StartedAt', 'CompletedAt']
        dynamic_headers = [f"Question {i + 1}" for i in range(len(questions))]
        writer.writerow(static_headers + dynamic_headers)

        # Optimize DB query: fetch all completed ResponseSets for the baseline questionnaire
        qs = ResponseSet.objects.filter(
            questionnaire__is_baseline=True, 
            status='COMPLETED'
        )

        group_name = request.query_params.get('group')
        if group_name:
            qs = qs.filter(user__group__name=group_name)

        response_sets = qs.select_related(
            'user', 'user__group', 'questionnaire'
        ).prefetch_related(
            'responses__question', 'responses__selected_option'
        )

        for rs in response_sets:
            # Map question ID -> response for quick lookup
            resp_dict = {ans.question_id: ans for ans in rs.responses.all()}
            
            row = [
                rs.user.user_id,
                rs.user.username,
                rs.user.group.name if rs.user.group else 'None',
                rs.started_at.strftime('%Y-%m-%d %H:%M:%S') if rs.started_at else '',
                rs.completed_at.strftime('%Y-%m-%d %H:%M:%S') if rs.completed_at else '',
            ]
            
            for q in questions:
                ans = resp_dict.get(q.id)
                if ans:
                    if ans.selected_option:
                        # Append the textual label per identical user instruction
                        row.append(ans.selected_option.label)
                    elif ans.text_value:
                        row.append(ans.text_value.replace('\n', ' '))
                    else:
                        row.append('')
                else:
                    row.append('')
                    
            writer.writerow(row)

        return response

class AdminDashboardAnalyticsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        import datetime
        from django.utils import timezone
        from questionnaires.models import ResponseSet
        from phases.models import Phase

        user_qs = User.objects.filter(is_superuser=False)
        total_participants = user_qs.count()

        completed_baselines = ResponseSet.objects.filter(status='COMPLETED').count()
        total_activities = Submission.objects.count()
        total_submissions = completed_baselines + total_activities

        seven_days_ago = timezone.now() - datetime.timedelta(days=7)
        
        # Submissions in last 7 days to calculate active rate
        active_baseline_users = ResponseSet.objects.filter(status='COMPLETED', completed_at__gte=seven_days_ago).values_list('user_id', flat=True)
        active_activity_users = Submission.objects.filter(submission_date__gte=seven_days_ago).values_list('user_id', flat=True)
        active_users = set(active_baseline_users) | set(active_activity_users)
        active_rate = round((len(active_users) / total_participants * 100), 1) if total_participants > 0 else 0

        # Phase Status
        today = timezone.now().date()
        current_phase = Phase.objects.filter(start_date__lte=today, end_date__gte=today).first()
        current_phase_name = current_phase.name if current_phase else "Pre-Launch"

        # Engagement Trend (last 7 days grouped by date)
        # We query day by day for the last 7 days
        engagement_trend = []
        for i in range(6, -1, -1):
            day_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=i)
            day_end = day_start + datetime.timedelta(days=1)
            b_count = ResponseSet.objects.filter(status='COMPLETED', completed_at__gte=day_start, completed_at__lt=day_end).count()
            a_count = Submission.objects.filter(submission_date__gte=day_start, submission_date__lt=day_end).count()
            
            engagement_trend.append({
                'date': day_start.strftime('%a %d'), 
                'count': b_count + a_count
            })

        # Recent Participants
        recent_users_qs = user_qs.select_related('group').order_by('-created_at')[:8]
        recent_participants = []
        for u in recent_users_qs:
            b_count = u.responseset_set.filter(status='COMPLETED').count() if hasattr(u, 'responseset_set') else 0
            a_count = u.submissions.count() if hasattr(u, 'submissions') else 0
            
            recent_participants.append({
                'id': u.id,
                'username': u.username,
                'group': u.group.name if hasattr(u, 'group') and u.group else 'Unassigned',
                'submissions_count': f"{b_count + a_count}/30", # format for dashboard out of 30
                'status': 'Active' if u.id in active_users else 'Inactive'
            })

        return Response({
            'total_participants': total_participants,
            'total_submissions': total_submissions,
            'active_rate_percentage': active_rate,
            'current_phase_name': current_phase_name,
            'engagement_trend': engagement_trend,
            'recent_participants': recent_participants
        })
