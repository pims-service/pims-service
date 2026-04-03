import csv
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from users.models import User
from activities.models import Submission
from questionnaires.models import QuestionnaireResponse

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
