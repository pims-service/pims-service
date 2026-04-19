import csv
import io
from celery import shared_task
from django.core.files.base import ContentFile
from .models import ExportTask

@shared_task
def generate_baseline_export_csv(task_id):
    try:
        task = ExportTask.objects.get(id=task_id)
        task.status = 'PROCESSING'
        task.save()

        from questionnaires.models import ResponseSet, Question
        
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        
        # Get ordered questions for the baseline questionnaire to act as columns
        questions = list(Question.objects.filter(questionnaire__is_baseline=True).order_by('order'))

        # Header for Wide Format
        static_headers = ['ParticipantID', 'Username', 'Group', 'StartedAt', 'CompletedAt']
        dynamic_headers = [f"Question {i + 1}" for i in range(len(questions))]
        writer.writerow(static_headers + dynamic_headers)

        # Optimize DB query: fetch all completed ResponseSets for the baseline questionnaire
        qs = ResponseSet.objects.filter(
            questionnaire__is_baseline=True, 
            status='COMPLETED'
        )

        # Apply filters from task metadata
        group_name = task.filters.get('group')
        if group_name and group_name != 'All':
            qs = qs.filter(user__group__name=group_name)

        response_sets = qs.select_related(
            'user', 'user__group', 'questionnaire'
        ).prefetch_related(
            'responses__question', 'responses__selected_option'
        )

        for rs in response_sets:
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
                        row.append(ans.selected_option.label)
                    elif ans.text_value:
                        row.append(ans.text_value.replace('\n', ' '))
                    else:
                        row.append('')
                else:
                    row.append('')
            
            writer.writerow(row)

        # Save the CSV to the FileField
        file_name = f"baseline_export_{task.id}.csv"
        task.file.save(file_name, ContentFile(output.getvalue().encode('utf-8')))
        task.status = 'SUCCESS'
        task.save()
        
    except Exception as e:
        try:
            task = ExportTask.objects.get(id=task_id)
            task.status = 'FAILED'
            task.error_message = str(e)
            task.save()
        except:
            pass
        raise e
