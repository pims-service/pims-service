import csv
import io
import logging
from celery import shared_task
from django.core.files.base import ContentFile
from .models import ExportTask

logger = logging.getLogger(__name__)

@shared_task
def generate_baseline_export_csv(task_id):
    try:
        task = ExportTask.objects.get(id=task_id)
        task.status = 'PROCESSING'
        task.save()

        import re
        from questionnaires.models import Question, ResponseSet, Response
        from django.contrib.auth import get_user_model
        from django.core.files.base import ContentFile

        # 1. Fetch and configure sociodemographic questions
        socio_questions = list(Question.objects.filter(questionnaire__assessment_type='SOCIODEMOGRAPHIC').order_by('order'))
        for q in socio_questions:
            content_lower = q.content.lower()
            if 'gender' in content_lower:
                q.header_name = 'Socio_Gender'
            elif 'age' in content_lower:
                q.header_name = 'Socio_Age'
            elif 'employment' in content_lower:
                q.header_name = 'Socio_Employment'
            elif 'education' in content_lower:
                q.header_name = 'Socio_Education'
            else:
                q.header_name = f"Socio_Q{q.order}"

        # 2. Fetch and configure psychometric questions
        psy_questions = list(Question.objects.filter(questionnaire__assessment_type='PSYCHOMETRIC').order_by('order'))

        # 3. Build CSV Headers
        headers = ['ParticipantID', 'Username', 'WhatsAppNumber', 'Group', 'DateOfBirth', 'RegistrationDate', 'BaselineCompletedAt']
        headers += [q.header_name for q in socio_questions]
        
        psy_columns = []
        for q in psy_questions:
            match = re.match(r'^\[([^\]]+)\]', q.content)
            tag = re.sub(r'[^a-zA-Z0-9\-]', '', match.group(1)).upper() if match else "PSYCH"
            headers.append(f"{tag}_Q{q.order}_SIGNUP")
            psy_columns.append(q.id)

        # 4. Fetch Users who have completed baseline
        User = get_user_model()
        users_qs = User.objects.filter(
            is_active=True,
            has_completed_baseline=True
        ).select_related('group').order_by('user_id')

        group_name = task.filters.get('group')
        if group_name and group_name != 'All':
            users_qs = users_qs.filter(group__name=group_name)

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)

        from django.db.models import Q

        for user in users_qs.iterator(chunk_size=1000):
            # Fetch completed responses at SIGNUP or SOCIODEMOGRAPHIC
            responses = Response.objects.filter(
                Q(response_set__questionnaire__assessment_type='SOCIODEMOGRAPHIC') |
                Q(response_set__milestone='SIGNUP'),
                response_set__user=user,
                response_set__status='COMPLETED'
            ).select_related('response_set', 'question', 'selected_option')

            resp_map = {}
            for r in responses:
                if r.response_set.questionnaire.assessment_type == 'SOCIODEMOGRAPHIC':
                    resp_map[r.question_id] = r
                elif r.response_set.milestone == 'SIGNUP':
                    resp_map[r.question_id] = r

            row = [
                user.user_id,
                user.username,
                user.whatsapp_number,
                user.group.name if user.group else 'None',
                user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else '',
                user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
                user.baseline_completed_at.strftime('%Y-%m-%d %H:%M:%S') if user.baseline_completed_at else '',
            ]

            # Socio answers
            for q in socio_questions:
                ans = resp_map.get(q.id)
                if ans:
                    val = ans.selected_option.label if ans.selected_option else (ans.text_value or '')
                    row.append(val.replace('\n', ' '))
                else:
                    row.append('')

            # Psy answers at SIGNUP
            for q_id in psy_columns:
                ans = resp_map.get(q_id)
                if ans:
                    val = ans.selected_option.label if ans.selected_option else (ans.text_value or '')
                    row.append(val.replace('\n', ' '))
                else:
                    row.append('')

            writer.writerow(row)

        file_name = f"baseline_export_{task.id}.csv"
        task.file.save(file_name, ContentFile(output.getvalue().encode('utf-8')))
        task.status = 'SUCCESS'
        task.save()
        
    except Exception as e:
        logger.error(f"Error generating baseline export CSV for task {task_id}: {e}")
        try:
            task = ExportTask.objects.get(id=task_id)
            task.status = 'FAILED'
            task.error_message = str(e)
            task.save()
        except Exception as task_update_error:
            logger.error(f"Failed to update task {task_id} status to FAILED: {task_update_error}")
        raise e

@shared_task
def generate_posttest_export_csv(task_id):
    try:
        task = ExportTask.objects.get(id=task_id)
        task.status = 'PROCESSING'
        task.save()

        import re
        from questionnaires.models import Question, ResponseSet, Response
        from django.contrib.auth import get_user_model
        from django.core.files.base import ContentFile

        # 1. Fetch and configure psychometric questions
        psy_questions = list(Question.objects.filter(questionnaire__assessment_type='PSYCHOMETRIC').order_by('order'))

        # 2. Build CSV Headers
        headers = ['ParticipantID', 'Username', 'Group', 'DateOfBirth', 'PosttestStartedAt', 'PosttestCompletedAt']
        
        psy_columns = []
        for q in psy_questions:
            match = re.match(r'^\[([^\]]+)\]', q.content)
            tag = re.sub(r'[^a-zA-Z0-9\-]', '', match.group(1)).upper() if match else "PSYCH"
            headers.append(f"{tag}_Q{q.order}_7_DAYS")
            psy_columns.append(q.id)

        # 3. Fetch Users who have completed the 7_DAYS milestone
        User = get_user_model()
        users_qs = User.objects.filter(
            is_active=True,
            response_sets__milestone='7_DAYS',
            response_sets__status='COMPLETED'
        ).select_related('group').distinct().order_by('user_id')

        group_name = task.filters.get('group')
        if group_name and group_name != 'All':
            users_qs = users_qs.filter(group__name=group_name)

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)

        for user in users_qs.iterator(chunk_size=1000):
            rs_7days = ResponseSet.objects.filter(
                user=user,
                milestone='7_DAYS',
                status='COMPLETED'
            ).first()

            if not rs_7days:
                continue

            responses = Response.objects.filter(
                response_set=rs_7days
            ).select_related('question', 'selected_option')

            resp_map = {r.question_id: r for r in responses}

            row = [
                user.user_id,
                user.username,
                user.group.name if user.group else 'None',
                user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else '',
                rs_7days.started_at.strftime('%Y-%m-%d %H:%M:%S') if rs_7days.started_at else '',
                rs_7days.completed_at.strftime('%Y-%m-%d %H:%M:%S') if rs_7days.completed_at else '',
            ]

            # Psy answers at 7_DAYS
            for q_id in psy_columns:
                ans = resp_map.get(q_id)
                if ans:
                    val = ans.selected_option.label if ans.selected_option else (ans.text_value or '')
                    row.append(val.replace('\n', ' '))
                else:
                    row.append('')

            writer.writerow(row)

        file_name = f"posttest_export_{task.id}.csv"
        task.file.save(file_name, ContentFile(output.getvalue().encode('utf-8')))
        task.status = 'SUCCESS'
        task.save()
        
    except Exception as e:
        logger.error(f"Error generating posttest export CSV for task {task_id}: {e}")
        try:
            task = ExportTask.objects.get(id=task_id)
            task.status = 'FAILED'
            task.error_message = str(e)
            task.save()
        except Exception as task_update_error:
            logger.error(f"Failed to update task {task_id} status to FAILED: {task_update_error}")
        raise e


@shared_task
def generate_longitudinal_export_csv(task_id):
    import tempfile
    import os
    import re
    from django.core.files import File
    from django.contrib.auth import get_user_model
    from questionnaires.models import Question, ResponseSet, Response

    try:
        task = ExportTask.objects.get(id=task_id)
        task.status = 'PROCESSING'
        task.save()

        # 1. Fetch and configure sociodemographic questions
        socio_questions = list(Question.objects.filter(questionnaire__assessment_type='SOCIODEMOGRAPHIC').order_by('order'))
        for q in socio_questions:
            content_lower = q.content.lower()
            if 'gender' in content_lower:
                header_name = 'Socio_Gender'
            elif 'age' in content_lower:
                header_name = 'Socio_Age'
            elif 'employment' in content_lower:
                header_name = 'Socio_Employment'
            elif 'education' in content_lower:
                header_name = 'Socio_Education'
            else:
                header_name = f"Socio_Q{q.order}"
            q.header_name = header_name

        # 2. Fetch and configure psychometric questions
        psy_questions = list(Question.objects.filter(questionnaire__assessment_type='PSYCHOMETRIC').order_by('order'))

        # 3. Build CSV Headers
        headers = ['ParticipantID', 'Username', 'Group', 'DateOfBirth', 'RegistrationDate', 'BaselineCompletedAt']
        headers += [q.header_name for q in socio_questions]

        # Map tuples of (question_id, milestone) to columns
        psy_columns = []
        milestones = ['SIGNUP', '7_DAYS', '3_MONTHS', '6_MONTHS', '1_YEAR']
        for milestone in milestones:
            for q in psy_questions:
                match = re.match(r'^\[([^\]]+)\]', q.content)
                tag = re.sub(r'[^a-zA-Z0-9\-]', '', match.group(1)).upper() if match else "PSYCH"
                headers.append(f"{tag}_Q{q.order}_{milestone}")
                psy_columns.append((q.id, milestone))

        # 4. Fetch Users
        User = get_user_model()
        users_qs = User.objects.filter(
            is_active=True,
            has_completed_baseline=True
        ).select_related('group').order_by('user_id')

        group_name = task.filters.get('group')
        if group_name and group_name != 'All':
            users_qs = users_qs.filter(group__name=group_name)

        # 5. Write to a Temporary File (O(1) memory overhead)
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, newline='', suffix='.csv', encoding='utf-8') as temp_file:
            writer = csv.writer(temp_file, quoting=csv.QUOTE_ALL)
            writer.writerow(headers)

            for user in users_qs.iterator(chunk_size=1000):
                # Fetch all completed responses for this user in a single optimized query
                responses = Response.objects.filter(
                    response_set__user=user,
                    response_set__status='COMPLETED'
                ).select_related('response_set', 'question', 'selected_option')

                resp_map = {}
                for r in responses:
                    m = r.response_set.milestone
                    if r.response_set.questionnaire.assessment_type == 'SOCIODEMOGRAPHIC':
                        resp_map[r.question_id] = r
                    else:
                        resp_map[(r.question_id, m)] = r

                row = [
                    user.user_id,
                    user.username,
                    user.group.name if user.group else 'None',
                    user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else '',
                    user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
                    user.baseline_completed_at.strftime('%Y-%m-%d %H:%M:%S') if user.baseline_completed_at else '',
                ]

                # Append sociodemographic values
                for q in socio_questions:
                    ans = resp_map.get(q.id)
                    if ans:
                        val = ans.selected_option.label if ans.selected_option else (ans.text_value or '')
                        row.append(val.replace('\n', ' '))
                    else:
                        row.append('')

                # Append psychometric values
                for q_id, milestone in psy_columns:
                    ans = resp_map.get((q_id, milestone))
                    if ans:
                        val = ans.selected_option.label if ans.selected_option else (ans.text_value or '')
                        row.append(val.replace('\n', ' '))
                    else:
                        row.append('')

                writer.writerow(row)

            temp_file_path = temp_file.name

        # 6. Save the temporary file to the Task model
        with open(temp_file_path, 'rb') as f:
            file_name = f"longitudinal_export_{task.id}.csv"
            task.file.save(file_name, File(f))

        task.status = 'SUCCESS'
        task.save()

        # Clean up temporary file
        os.unlink(temp_file_path)

    except Exception as e:
        logger.error(f"Error generating longitudinal export CSV for task {task_id}: {e}")
        try:
            task = ExportTask.objects.get(id=task_id)
            task.status = 'FAILED'
            task.error_message = str(e)
            task.save()
        except Exception as task_update_error:
            logger.error(f"Failed to update task {task_id} status to FAILED: {task_update_error}")
        raise e
