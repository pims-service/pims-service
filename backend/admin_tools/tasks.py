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

        from questionnaires.models import Question, ResponseSet, Response
        from django.contrib.auth import get_user_model
        from django.core.files.base import ContentFile
        from admin_tools.export_utils import (
            build_psych_item_headers_and_columns,
            append_psych_item_values,
            append_perma_score_values,
            extend_headers_with_perma_scores,
        )

        # 1. Fetch and configure psychometric questions
        psy_questions = list(Question.objects.filter(questionnaire__assessment_type='PSYCHOMETRIC').order_by('order'))

        # 2. Build CSV Headers
        headers = ['ParticipantID', 'Username', 'Group', 'DateOfBirth', 'T0StartedAt', 'T0CompletedAt']
        item_headers, psy_columns = build_psych_item_headers_and_columns(psy_questions, 'SIGNUP')
        headers.extend(item_headers)
        extend_headers_with_perma_scores(headers, 'SIGNUP')

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

            append_psych_item_values(row, resp_map, psy_columns)
            append_perma_score_values(row, rs_t0)

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
    from django.core.files import File
    from django.contrib.auth import get_user_model
    from questionnaires.models import Question, ResponseSet, Response
    from admin_tools.export_utils import (
        build_psych_item_headers_and_columns,
        append_psych_item_values,
        append_perma_score_values,
        extend_headers_with_perma_scores,
    )

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
            item_headers, question_ids = build_psych_item_headers_and_columns(psy_questions, milestone)
            headers.extend(item_headers)
            psy_columns.extend((q_id, milestone) for q_id in question_ids)

        for milestone in milestones:
            extend_headers_with_perma_scores(headers, milestone)

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

                for milestone in milestones:
                    rs = ResponseSet.objects.filter(
                        user=user,
                        milestone=milestone,
                        questionnaire__assessment_type='PSYCHOMETRIC',
                        status='COMPLETED',
                    ).first()
                    append_perma_score_values(row, rs)

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

        from questionnaires.models import Question, ResponseSet, Response
        from django.contrib.auth import get_user_model
        from django.core.files.base import ContentFile
        from admin_tools.export_utils import (
            build_psych_item_headers_and_columns,
            append_psych_item_values,
            append_perma_score_values,
            extend_headers_with_perma_scores,
        )

        # 1. Fetch and configure psychometric questions
        psy_questions = list(Question.objects.filter(questionnaire__assessment_type='PSYCHOMETRIC').order_by('order'))

        # 2. Build CSV Headers
        headers = ['ParticipantID', 'Username', 'Group', 'DateOfBirth', 'T1StartedAt', 'T1CompletedAt']
        item_headers, psy_columns = build_psych_item_headers_and_columns(psy_questions, '7_DAYS')
        headers.extend(item_headers)
        extend_headers_with_perma_scores(headers, '7_DAYS')

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

            append_psych_item_values(row, resp_map, psy_columns)
            append_perma_score_values(row, rs_t1)

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

        import io
        import csv
        from questionnaires.models import Question, ResponseSet, Response
        from django.contrib.auth import get_user_model
        from django.core.files.base import ContentFile
        from admin_tools.export_utils import (
            build_psych_item_headers_and_columns,
            append_psych_item_values,
            append_perma_score_values,
            extend_headers_with_perma_scores,
        )

        # 1. Fetch psychometric questions
        psy_questions = list(Question.objects.filter(questionnaire__assessment_type='PSYCHOMETRIC').order_by('order'))

        # 2. Build CSV Headers
        headers = ['ParticipantID', 'Username', 'Group', 'DateOfBirth', 'T2StartedAt', 'T2CompletedAt']
        item_headers, psy_columns = build_psych_item_headers_and_columns(psy_questions, '90_DAYS')
        headers.extend(item_headers)
        extend_headers_with_perma_scores(headers, '90_DAYS')

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
            append_psych_item_values(row, resp_map, psy_columns)
            append_perma_score_values(row, rs_t2)
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

        import io
        import csv
        from questionnaires.models import Question, ResponseSet, Response
        from django.contrib.auth import get_user_model
        from django.core.files.base import ContentFile
        from admin_tools.export_utils import (
            build_psych_item_headers_and_columns,
            append_psych_item_values,
            append_perma_score_values,
            extend_headers_with_perma_scores,
        )

        # 1. Fetch psychometric questions
        psy_questions = list(Question.objects.filter(questionnaire__assessment_type='PSYCHOMETRIC').order_by('order'))

        # 2. Build CSV Headers
        headers = ['ParticipantID', 'Username', 'Group', 'DateOfBirth', 'T3StartedAt', 'T3CompletedAt']
        item_headers, psy_columns = build_psych_item_headers_and_columns(psy_questions, '6_MONTHS')
        headers.extend(item_headers)
        extend_headers_with_perma_scores(headers, '6_MONTHS')

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
            append_psych_item_values(row, resp_map, psy_columns)
            append_perma_score_values(row, rs_t3)
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
