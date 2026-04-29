import csv
from django.http import StreamingHttpResponse
from rest_framework import views, permissions, status, response
from django.shortcuts import get_object_or_404
from .models import Questionnaire, ResponseSet
from .services import QuestionnaireExportService

class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value

class QuestionnaireExportView(views.APIView):
    """
    View to export questionnaire results in a wide-format CSV.
    Optimized with StreamingHttpResponse for large datasets.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, pk):
        questionnaire = get_object_or_404(Questionnaire, pk=pk)
        
        headers, data_rows = QuestionnaireExportService.get_wide_format_data(questionnaire.id)
        
        if headers is None:
            return response.Response(
                {"error": "Questionnaire not found or had no valid structure."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Streaming CSV implementation
        def iter_items(headers, rows):
            buffer = Echo()
            writer = csv.writer(buffer)
            yield writer.writerow(headers)
            for row in rows:
                yield writer.writerow(row)

        resp = StreamingHttpResponse(
            iter_items(headers, data_rows),
            content_type="text/csv"
        )
        filename = f"export_{questionnaire.title.replace(' ', '_')}_{pk}.csv"
        resp['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return resp

class QuestionnaireAnalyticsSummaryView(views.APIView):
    """
    Provides a JSON summary of questionnaire completion and basic stats.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, pk):
        questionnaire = get_object_or_404(Questionnaire, pk=pk)
        attempts = questionnaire.attempts.all()
        
        total_attempts = attempts.count()
        completed_attempts = attempts.filter(status='COMPLETED').count()
        
        # Calculate completion rate
        completion_rate = (completed_attempts / total_attempts * 100) if total_attempts > 0 else 0
        
        return response.Response({
            "questionnaire_title": questionnaire.title,
            "total_starts": total_attempts,
            "total_completions": completed_attempts,
            "completion_rate_percentage": round(completion_rate, 2),
        })

class GlobalQuestionnaireAnalyticsView(views.APIView):
    """
    Provides a JSON summary of completion and basic stats for ALL questionnaires.
    Used by the Experimental Reports dashboard.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        questionnaires = Questionnaire.objects.filter(is_active=True)
        results = []

        for q in questionnaires:
            attempts = q.attempts.all()
            total = attempts.count()
            completed = attempts.filter(status='COMPLETED').count()
            rate = (completed / total * 100) if total > 0 else 0

            results.append({
                "questionnaire_id": str(q.id),
                "title": q.title,
                "total_starts": total,
                "total_completions": completed,
                "completion_rate": round(rate, 2),
            })

        return response.Response(results)
