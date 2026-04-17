import csv
from django.db.models import Prefetch
from django.utils import timezone
from .models import Questionnaire, Question, ResponseSet, Response, Option

class QuestionnaireExportService:
    """
    Service to handle the transformation of normalized questionnaire responses
    into a flat, wide-format structure suitable for SPSS/R and CSV export.
    """

    @staticmethod
    def get_wide_format_data(questionnaire_id):
        """
        Retrieves all completed responses for a questionnaire and pivots them.
        Returns: (headers, data_rows)
        """
        # 1. Fetch questionnaire and its questions (in order)
        try:
            questionnaire = Questionnaire.objects.prefetch_related('questions').get(id=questionnaire_id)
        except Questionnaire.DoesNotExist:
            return None, None

        questions = list(questionnaire.questions.all().order_by('order'))
        
        # 2. Define Headers
        # Metadata headers
        headers = [
            'ResponseSet_ID', 'User_ID', 'Username', 'Full_Name', 
            'Group_Name', 'Status', 'Started_At', 'Completed_At', 
            'Duration_Seconds'
        ]
        
        # Question headers (using ID to ensure uniqueness, but content can be metadata)
        # In SPSS, it's common to use 'Q1', 'Q2', etc. with labels.
        # We'll use Question ID as the column name for now.
        for q in questions:
            headers.append(f"Q_{q.id}")

        # 3. Fetch all completed response sets with prefetch for responses
        # Highly optimized: one query for ResponseSets, one for User/Group, one for Responses/Options
        response_sets = ResponseSet.objects.filter(
            questionnaire_id=questionnaire_id,
            status='COMPLETED'
        ).select_related('user', 'user__group').prefetch_related(
            Prefetch('responses', queryset=Response.objects.select_related('question', 'selected_option'))
        ).order_by('-completed_at')

        # 4. Pivot Data
        data_rows = []
        for rs in response_sets:
            # Metadata
            duration = 0
            if rs.completed_at and rs.started_at:
                duration = (rs.completed_at - rs.started_at).total_seconds()

            row = [
                rs.id,
                rs.user.id,
                rs.user.username,
                rs.user.full_name,
                rs.user.group.name if rs.user.group else 'None',
                rs.status,
                rs.started_at.strftime('%Y-%m-%d %H:%M:%S'),
                rs.completed_at.strftime('%Y-%m-%d %H:%M:%S') if rs.completed_at else '',
                round(duration, 2)
            ]

            # Pivot Responses
            # Map question_id -> response for this set
            answers_map = {resp.question_id: resp for resp in rs.responses.all()}
            
            for q in questions:
                answer = answers_map.get(q.id)
                if answer:
                    if q.type in ['CHOICE', 'SCALE'] and answer.selected_option:
                        # CORE: Export numeric value for SPSS
                        row.append(answer.selected_option.numeric_value)
                    else:
                        # Export text value (sanitize for CSV)
                        val = answer.text_value or ""
                        row.append(val.replace('\n', ' ').replace('\r', ''))
                else:
                    # Missing value
                    row.append(None)
            
            data_rows.append(row)

        return headers, data_rows
