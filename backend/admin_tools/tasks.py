import csv
import io
import logging
from celery import shared_task
from django.core.files.base import ContentFile
from .models import ExportTask

logger = logging.getLogger(__name__)



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
        headers = ['ParticipantID', 'Username', 'Group', 'DateOfBirth', 'T0StartedAt', 'T0CompletedAt']
        
        psy_columns = []
        perma_codes = ["A1", "E1", "P1", "N1", "A2", "H1", "M1", "R1", "M2", "E2", "Lon", "H2", "P2", "N2", "A3", "N3", "E3", "H3", "R2", "M3", "R3", "P3", "Hap"]
        tag_counters = {}
        for q in psy_questions:
            match = re.match(r'^\[([^\]]+)\]', q.content)
            tag = re.sub(r'[^a-zA-Z0-9]', '', match.group(1)).upper() if match else "PSYCH"
            tag_counters[tag] = tag_counters.get(tag, 0) + 1
            relative_order = tag_counters[tag]
            
            if tag == "PERMA":
                code = perma_codes[relative_order - 1]
                header_name = f"PERMA_{code.upper()}_SIGNUP"
            else:
                header_name = f"{tag}_Q{relative_order}_SIGNUP"
                
            headers.append(header_name)
            psy_columns.append(q.id)

        # 3. Fetch Users who have completed the SIGNUP milestone baseline psychometrics
        User = get_user_model()
        users_qs = User.objects.filter(
            is_active=True,
            response_sets__milestone='SIGNUP',
            response_sets__questionnaire__assessment_type='PSYCHOMETRIC',
            response_sets__status='COMPLETED'
        ).select_related('group').distinct().order_by('user_id')

        group_name = task.filters.get('group')
        if group_name and group_name != 'All':
            users_qs = users_qs.filter(group__name=group_name)

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)

        for user in users_qs.iterator(chunk_size=1000):
            rs_t0 = ResponseSet.objects.filter(
                user=user,
                milestone='SIGNUP',
                questionnaire__assessment_type='PSYCHOMETRIC',
                status='COMPLETED'
            ).first()

            if not rs_t0:
                continue

            responses = Response.objects.filter(
                response_set=rs_t0
            ).select_related('question', 'selected_option')

            resp_map = {r.question_id: r for r in responses}

            row = [
                user.user_id,
                user.username,
                user.group.name if user.group else 'None',
                user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else '',
                rs_t0.started_at.strftime('%Y-%m-%d %H:%M:%S') if rs_t0.started_at else '',
                rs_t0.completed_at.strftime('%Y-%m-%d %H:%M:%S') if rs_t0.completed_at else '',
            ]

            # Psy answers at SIGNUP
            for q_id in psy_columns:
                ans = resp_map.get(q_id)
                if ans:
                    val = ans.selected_option.label if ans.selected_option else (ans.text_value or '')
                    row.append(val.replace('\n', ' '))
                else:
                    row.append('')

            writer.writerow(row)

        file_name = f"t0_export_{task.id}.csv"
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
        perma_codes = ["A1", "E1", "P1", "N1", "A2", "H1", "M1", "R1", "M2", "E2", "Lon", "H2", "P2", "N2", "A3", "N3", "E3", "H3", "R2", "M3", "R3", "P3", "Hap"]
        
        for milestone in milestones:
            tag_counters = {}
            for q in psy_questions:
                match = re.match(r'^\[([^\]]+)\]', q.content)
                tag = re.sub(r'[^a-zA-Z0-9]', '', match.group(1)).upper() if match else "PSYCH"
                tag_counters[tag] = tag_counters.get(tag, 0) + 1
                relative_order = tag_counters[tag]
                
                if tag == "PERMA":
                    code = perma_codes[relative_order - 1]
                    header_name = f"PERMA_{code.upper()}_{milestone}"
                else:
                    header_name = f"{tag}_Q{relative_order}_{milestone}"
                    
                headers.append(header_name)
                psy_columns.append((q.id, milestone))

        # 4. Fetch Users
        User = get_user_model()
        users_qs = User.objects.filter(
            is_active=True,
            has_completed_sociodemographic=True
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
                    user.onboarding_completed_at.strftime('%Y-%m-%d %H:%M:%S') if user.onboarding_completed_at else '',
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


@shared_task
def generate_t1_export_csv(task_id):
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
        headers = ['ParticipantID', 'Username', 'Group', 'DateOfBirth', 'T1StartedAt', 'T1CompletedAt']
        
        psy_columns = []
        perma_codes = ["A1", "E1", "P1", "N1", "A2", "H1", "M1", "R1", "M2", "E2", "Lon", "H2", "P2", "N2", "A3", "N3", "E3", "H3", "R2", "M3", "R3", "P3", "Hap"]
        tag_counters = {}
        for q in psy_questions:
            match = re.match(r'^\[([^\]]+)\]', q.content)
            tag = re.sub(r'[^a-zA-Z0-9]', '', match.group(1)).upper() if match else "PSYCH"
            tag_counters[tag] = tag_counters.get(tag, 0) + 1
            relative_order = tag_counters[tag]
            
            if tag == "PERMA":
                code = perma_codes[relative_order - 1]
                header_name = f"PERMA_{code.upper()}_7_DAYS"
            else:
                header_name = f"{tag}_Q{relative_order}_7_DAYS"
                
            headers.append(header_name)
            psy_columns.append(q.id)

        # 3. Fetch Users who have completed the 7_DAYS milestone baseline psychometrics
        User = get_user_model()
        users_qs = User.objects.filter(
            is_active=True,
            response_sets__milestone='7_DAYS',
            response_sets__questionnaire__assessment_type='PSYCHOMETRIC',
            response_sets__status='COMPLETED'
        ).select_related('group').distinct().order_by('user_id')

        group_name = task.filters.get('group')
        if group_name and group_name != 'All':
            users_qs = users_qs.filter(group__name=group_name)

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)

        for user in users_qs.iterator(chunk_size=1000):
            rs_t1 = ResponseSet.objects.filter(
                user=user,
                milestone='7_DAYS',
                questionnaire__assessment_type='PSYCHOMETRIC',
                status='COMPLETED'
            ).first()

            if not rs_t1:
                continue

            responses = Response.objects.filter(
                response_set=rs_t1
            ).select_related('question', 'selected_option')

            resp_map = {r.question_id: r for r in responses}

            row = [
                user.user_id,
                user.username,
                user.group.name if user.group else 'None',
                user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else '',
                rs_t1.started_at.strftime('%Y-%m-%d %H:%M:%S') if rs_t1.started_at else '',
                rs_t1.completed_at.strftime('%Y-%m-%d %H:%M:%S') if rs_t1.completed_at else '',
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

        file_name = f"t1_export_{task.id}.csv"
        task.file.save(file_name, ContentFile(output.getvalue().encode('utf-8')))
        task.status = 'SUCCESS'
        task.save()
        
    except Exception as e:
        logger.error(f"Error generating T1 export CSV for task {task_id}: {e}")
        try:
            task = ExportTask.objects.get(id=task_id)
            task.status = 'FAILED'
            task.error_message = str(e)
            task.save()
        except Exception as task_update_error:
            logger.error(f"Failed to update task {task_id} status to FAILED: {task_update_error}")
        raise e


@shared_task
def generate_t2_export_csv(task_id):
    try:
        task = ExportTask.objects.get(id=task_id)
        task.status = 'PROCESSING'
        task.save()

        import re
        import io
        import csv
        from questionnaires.models import Question, ResponseSet, Response
        from django.contrib.auth import get_user_model
        from django.core.files.base import ContentFile

        # 1. Fetch psychometric questions
        psy_questions = list(Question.objects.filter(questionnaire__assessment_type='PSYCHOMETRIC').order_by('order'))

        # 2. Build CSV Headers
        headers = ['ParticipantID', 'Username', 'Group', 'DateOfBirth', 'T2StartedAt', 'T2CompletedAt']
        psy_columns = []
        perma_codes = ["A1", "E1", "P1", "N1", "A2", "H1", "M1", "R1", "M2", "E2", "Lon", "H2", "P2", "N2", "A3", "N3", "E3", "H3", "R2", "M3", "R3", "P3", "Hap"]
        tag_counters = {}
        for q in psy_questions:
            match = re.match(r'^\[([^\]]+)\]', q.content)
            tag = re.sub(r'[^a-zA-Z0-9]', '', match.group(1)).upper() if match else "PSYCH"
            tag_counters[tag] = tag_counters.get(tag, 0) + 1
            relative_order = tag_counters[tag]
            if tag == "PERMA":
                code = perma_codes[relative_order - 1]
                header_name = f"PERMA_{code.upper()}_90_DAYS"
            else:
                header_name = f"{tag}_Q{relative_order}_90_DAYS"
            headers.append(header_name)
            psy_columns.append(q.id)

        # 3. Fetch Users who have completed the 3_MONTHS milestone psychometrics
        User = get_user_model()
        users_qs = User.objects.filter(
            is_active=True,
            response_sets__milestone='3_MONTHS',
            response_sets__questionnaire__assessment_type='PSYCHOMETRIC',
            response_sets__status='COMPLETED'
        ).select_related('group').distinct().order_by('user_id')
        group_name = task.filters.get('group')
        if group_name and group_name != 'All':
            users_qs = users_qs.filter(group__name=group_name)

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)

        for user in users_qs.iterator(chunk_size=1000):
            rs_t2 = ResponseSet.objects.filter(
                user=user,
                milestone='3_MONTHS',
                questionnaire__assessment_type='PSYCHOMETRIC',
                status='COMPLETED'
            ).first()
            if not rs_t2:
                continue
            responses = Response.objects.filter(response_set=rs_t2).select_related('question', 'selected_option')
            resp_map = {r.question_id: r for r in responses}
            row = [
                user.user_id,
                user.username,
                user.group.name if user.group else 'None',
                user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else '',
                rs_t2.started_at.strftime('%Y-%m-%d %H:%M:%S') if rs_t2.started_at else '',
                rs_t2.completed_at.strftime('%Y-%m-%d %H:%M:%S') if rs_t2.completed_at else '',
            ]
            for q_id in psy_columns:
                ans = resp_map.get(q_id)
                if ans:
                    val = ans.selected_option.label if ans.selected_option else (ans.text_value or '')
                    row.append(val.replace('\n', ' '))
                else:
                    row.append('')
            writer.writerow(row)

        file_name = f"t2_export_{task.id}.csv"
        task.file.save(file_name, ContentFile(output.getvalue().encode('utf-8')))
        task.status = 'SUCCESS'
        task.save()
    except Exception as e:
        logger.error(f"Error generating T2 export CSV for task {task_id}: {e}")
        try:
            task = ExportTask.objects.get(id=task_id)
            task.status = 'FAILED'
            task.error_message = str(e)
            task.save()
        except Exception as task_update_error:
            logger.error(f"Failed to update task {task_id} status to FAILED: {task_update_error}")
        raise e


@shared_task
def generate_t3_export_csv(task_id):
    try:
        task = ExportTask.objects.get(id=task_id)
        task.status = 'PROCESSING'
        task.save()

        import re
        import io
        import csv
        from questionnaires.models import Question, ResponseSet, Response
        from django.contrib.auth import get_user_model
        from django.core.files.base import ContentFile

        # 1. Fetch psychometric questions
        psy_questions = list(Question.objects.filter(questionnaire__assessment_type='PSYCHOMETRIC').order_by('order'))

        # 2. Build CSV Headers
        headers = ['ParticipantID', 'Username', 'Group', 'DateOfBirth', 'T3StartedAt', 'T3CompletedAt']
        psy_columns = []
        perma_codes = ["A1", "E1", "P1", "N1", "A2", "H1", "M1", "R1", "M2", "E2", "Lon", "H2", "P2", "N2", "A3", "N3", "E3", "H3", "R2", "M3", "R3", "P3", "Hap"]
        tag_counters = {}
        for q in psy_questions:
            match = re.match(r'^\[([^\]]+)\]', q.content)
            tag = re.sub(r'[^a-zA-Z0-9]', '', match.group(1)).upper() if match else "PSYCH"
            tag_counters[tag] = tag_counters.get(tag, 0) + 1
            relative_order = tag_counters[tag]
            if tag == "PERMA":
                code = perma_codes[relative_order - 1]
                header_name = f"PERMA_{code.upper()}_6_MONTHS"
            else:
                header_name = f"{tag}_Q{relative_order}_6_MONTHS"
            headers.append(header_name)
            psy_columns.append(q.id)

        # 3. Fetch Users who have completed the 6_MONTHS milestone psychometrics
        User = get_user_model()
        users_qs = User.objects.filter(
            is_active=True,
            response_sets__milestone='6_MONTHS',
            response_sets__questionnaire__assessment_type='PSYCHOMETRIC',
            response_sets__status='COMPLETED'
        ).select_related('group').distinct().order_by('user_id')
        group_name = task.filters.get('group')
        if group_name and group_name != 'All':
            users_qs = users_qs.filter(group__name=group_name)

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)

        for user in users_qs.iterator(chunk_size=1000):
            rs_t3 = ResponseSet.objects.filter(
                user=user,
                milestone='6_MONTHS',
                questionnaire__assessment_type='PSYCHOMETRIC',
                status='COMPLETED'
            ).first()
            if not rs_t3:
                continue
            responses = Response.objects.filter(response_set=rs_t3).select_related('question', 'selected_option')
            resp_map = {r.question_id: r for r in responses}
            row = [
                user.user_id,
                user.username,
                user.group.name if user.group else 'None',
                user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else '',
                rs_t3.started_at.strftime('%Y-%m-%d %H:%M:%S') if rs_t3.started_at else '',
                rs_t3.completed_at.strftime('%Y-%m-%d %H:%M:%S') if rs_t3.completed_at else '',
            ]
            for q_id in psy_columns:
                ans = resp_map.get(q_id)
                if ans:
                    val = ans.selected_option.label if ans.selected_option else (ans.text_value or '')
                    row.append(val.replace('\n', ' '))
                else:
                    row.append('')
            writer.writerow(row)

        file_name = f"t3_export_{task.id}.csv"
        task.file.save(file_name, ContentFile(output.getvalue().encode('utf-8')))
        task.status = 'SUCCESS'
        task.save()
    except Exception as e:
        logger.error(f"Error generating T3 export CSV for task {task_id}: {e}")
        try:
            task = ExportTask.objects.get(id=task_id)
            task.status = 'FAILED'
            task.error_message = str(e)
            task.save()
        except Exception as task_update_error:
            logger.error(f"Failed to update task {task_id} status to FAILED: {task_update_error}")
        raise e


@shared_task
def generate_t4_export_csv(task_id):
    try:
        task = ExportTask.objects.get(id=task_id)
        task.status = 'PROCESSING'
        task.save()

        import re
        import io
        import csv
        from questionnaires.models import Question, ResponseSet, Response
        from django.contrib.auth import get_user_model
        from django.core.files.base import ContentFile

        psy_questions = list(Question.objects.filter(questionnaire__assessment_type='PSYCHOMETRIC').order_by('order'))

        headers = ['ParticipantID', 'Username', 'Group', 'DateOfBirth', 'T4StartedAt', 'T4CompletedAt']
        psy_columns = []
        perma_codes = ["A1", "E1", "P1", "N1", "A2", "H1", "M1", "R1", "M2", "E2", "Lon", "H2", "P2", "N2", "A3", "N3", "E3", "H3", "R2", "M3", "R3", "P3", "Hap"]
        tag_counters = {}
        for q in psy_questions:
            match = re.match(r'^\[([^\]]+)\]', q.content)
            tag = re.sub(r'[^a-zA-Z0-9]', '', match.group(1)).upper() if match else "PSYCH"
            tag_counters[tag] = tag_counters.get(tag, 0) + 1
            relative_order = tag_counters[tag]
            if tag == "PERMA":
                code = perma_codes[relative_order - 1]
                header_name = f"PERMA_{code.upper()}_1_YEAR"
            else:
                header_name = f"{tag}_Q{relative_order}_1_YEAR"
            headers.append(header_name)
            psy_columns.append(q.id)

        User = get_user_model()
        users_qs = User.objects.filter(
            is_active=True,
            response_sets__milestone='1_YEAR',
            response_sets__questionnaire__assessment_type='PSYCHOMETRIC',
            response_sets__status='COMPLETED'
        ).select_related('group').distinct().order_by('user_id')
        group_name = task.filters.get('group')
        if group_name and group_name != 'All':
            users_qs = users_qs.filter(group__name=group_name)

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)

        for user in users_qs.iterator(chunk_size=1000):
            rs_t4 = ResponseSet.objects.filter(
                user=user,
                milestone='1_YEAR',
                questionnaire__assessment_type='PSYCHOMETRIC',
                status='COMPLETED'
            ).first()
            if not rs_t4:
                continue
            responses = Response.objects.filter(response_set=rs_t4).select_related('question', 'selected_option')
            resp_map = {r.question_id: r for r in responses}
            row = [
                user.user_id,
                user.username,
                user.group.name if user.group else 'None',
                user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else '',
                rs_t4.started_at.strftime('%Y-%m-%d %H:%M:%S') if rs_t4.started_at else '',
                rs_t4.completed_at.strftime('%Y-%m-%d %H:%M:%S') if rs_t4.completed_at else '',
            ]
            for q_id in psy_columns:
                ans = resp_map.get(q_id)
                if ans:
                    val = ans.selected_option.label if ans.selected_option else (ans.text_value or '')
                    row.append(val.replace('\n', ' '))
                else:
                    row.append('')
            writer.writerow(row)

        file_name = f"t4_export_{task.id}.csv"
        task.file.save(file_name, ContentFile(output.getvalue().encode('utf-8')))
        task.status = 'SUCCESS'
        task.save()
    except Exception as e:
        logger.error(f"Error generating T4 export CSV for task {task_id}: {e}")
        try:
            task = ExportTask.objects.get(id=task_id)
            task.status = 'FAILED'
            task.error_message = str(e)
            task.save()
        except Exception as task_update_error:
            logger.error(f"Failed to update task {task_id} status to FAILED: {task_update_error}")
        raise e
