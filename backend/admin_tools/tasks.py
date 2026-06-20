import csv
import io
import logging
from celery import shared_task
from django.core.files.base import ContentFile
from .models import ExportTask
from .export_utils import sanitize_csv_cell

logger = logging.getLogger(__name__)


def count_words(text):
    if not text:
        return 0
    return len(text.strip().split())


def get_submission_entries(sub):
    """
    Returns (entry_1, entry_2, entry_3) for a submission.
    If they are empty but content is populated, reconstruct them from content.
    """
    e1 = sub.entry_1 or ''
    e2 = sub.entry_2 or ''
    e3 = sub.entry_3 or ''
    
    if not (e1 or e2 or e3) and sub.content:
        parts = sub.content.split('\n\n---\n\n')
        if len(parts) >= 1:
            e1 = parts[0]
        if len(parts) >= 2:
            e2 = parts[1]
        if len(parts) >= 3:
            e3 = parts[2]
            
    return e1, e2, e3


def get_user_window_stats(user, activity_wave):
    """
    Queries Submission records for the user in that wave.
    Computes the 5 derived window variables.
    """
    from activities.models import Submission
    submissions = list(Submission.objects.filter(user=user, activity_wave=activity_wave))
    
    days_completed = len(submissions)
    non_empty_entries_count = 0
    total_words = 0
    total_duration = 0
    
    for sub in submissions:
        day_duration = (sub.entry_1_duration_sec or 0) + (sub.entry_2_duration_sec or 0) + (sub.entry_3_duration_sec or 0)
        total_duration += day_duration
        
        e1, e2, e3 = get_submission_entries(sub)
        for entry_text in [e1, e2, e3]:
            if entry_text and entry_text.strip():
                non_empty_entries_count += 1
                total_words += count_words(entry_text)
                
    mean_words_per_entry = (total_words / non_empty_entries_count) if non_empty_entries_count > 0 else 0.0
    mean_session_duration_sec = (total_duration / days_completed) if days_completed > 0 else 0.0
    
    return {
        'window_mean_words_per_entry': round(mean_words_per_entry, 2),
        'window_entries_completed': non_empty_entries_count,
        'window_days_completed': days_completed,
        'window_total_words': total_words,
        'window_mean_session_duration_sec': round(mean_session_duration_sec, 2),
    }


@shared_task(time_limit=300, soft_time_limit=240)
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
            append_battery_score_values,
            extend_headers_with_battery_scores,
        )

        # 1. Fetch and configure psychometric questions
        psy_questions = list(Question.objects.filter(questionnaire__assessment_type='PSYCHOMETRIC').order_by('order'))

        # 2. Build CSV Headers
        headers = ['ParticipantID', 'Username', 'Group', 'DateOfBirth', 'T0StartedAt', 'T0CompletedAt']
        item_headers, psy_columns = build_psych_item_headers_and_columns(psy_questions, 'SIGNUP')
        headers.extend(item_headers)
        extend_headers_with_battery_scores(headers, 'SIGNUP')

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
            append_battery_score_values(row, rs_t0)

            writer.writerow(row)

        file_name = f"onboarding_assessment_export_{task.id}.csv"
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


@shared_task(time_limit=300, soft_time_limit=240)
def generate_longitudinal_export_csv(task_id):
    import tempfile
    import os
    from django.core.files import File
    from django.contrib.auth import get_user_model
    from questionnaires.models import Question, ResponseSet, Response
    from admin_tools.export_utils import (
        build_psych_item_headers_and_columns,
        append_psych_item_values,
        append_battery_score_values,
        extend_headers_with_battery_scores,
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
        milestones = ['SIGNUP', '7_DAYS', '1_MONTH', '3_MONTHS', '6_MONTHS', '1_YEAR']

        for milestone in milestones:
            item_headers, question_ids = build_psych_item_headers_and_columns(psy_questions, milestone)
            headers.extend(item_headers)
            psy_columns.extend((q_id, milestone) for q_id in question_ids)

        for milestone in milestones:
            extend_headers_with_battery_scores(headers, milestone)

        milestone_waves = {
            '7_DAYS': 'PRE_T1',
            '1_MONTH': 'PRE_T_1M',
            '3_MONTHS': 'PRE_T2',
            '6_MONTHS': 'PRE_T3',
            '1_YEAR': 'PRE_T4'
        }

        for milestone in ['7_DAYS', '1_MONTH', '3_MONTHS', '6_MONTHS', '1_YEAR']:
            headers.extend([
                f"{milestone}_window_mean_words_per_entry",
                f"{milestone}_window_entries_completed",
                f"{milestone}_window_days_completed",
                f"{milestone}_window_total_words",
                f"{milestone}_window_mean_session_duration_sec"
            ])

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
                        row.append(sanitize_csv_cell(val.replace('\n', ' ')))
                    else:
                        row.append('')

                # Append psychometric values
                for q_id, milestone in psy_columns:
                    ans = resp_map.get((q_id, milestone))
                    if ans:
                        if ans.selected_option_value is not None:
                            val = str(ans.selected_option_value)
                        elif ans.selected_option:
                            val = str(ans.selected_option.numeric_value)
                        else:
                            val = ans.text_value or ''
                        row.append(sanitize_csv_cell(val.replace('\n', ' ')))
                    else:
                        row.append('')

                for milestone in milestones:
                    rs = ResponseSet.objects.filter(
                        user=user,
                        milestone=milestone,
                        questionnaire__assessment_type='PSYCHOMETRIC',
                        status='COMPLETED',
                    ).first()
                    append_battery_score_values(row, rs)

                for milestone in ['7_DAYS', '1_MONTH', '3_MONTHS', '6_MONTHS', '1_YEAR']:
                    wave = milestone_waves[milestone]
                    stats = get_user_window_stats(user, wave)
                    row.extend([
                        stats['window_mean_words_per_entry'],
                        stats['window_entries_completed'],
                        stats['window_days_completed'],
                        stats['window_total_words'],
                        stats['window_mean_session_duration_sec']
                    ])

                writer.writerow(row)

            temp_file_path = temp_file.name

        # 6. Save the temporary file to the Task model
        with open(temp_file_path, 'rb') as f:
            file_name = f"longitudinal_assessment_export_{task.id}.csv"
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


@shared_task(time_limit=300, soft_time_limit=240)
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
            append_battery_score_values,
            extend_headers_with_battery_scores,
        )

        # 1. Fetch and configure psychometric questions
        psy_questions = list(Question.objects.filter(questionnaire__assessment_type='PSYCHOMETRIC').order_by('order'))

        # 2. Build CSV Headers
        headers = ['ParticipantID', 'Username', 'Group', 'DateOfBirth', 'T1StartedAt', 'T1CompletedAt']
        item_headers, psy_columns = build_psych_item_headers_and_columns(psy_questions, '7_DAYS')
        headers.extend(item_headers)
        extend_headers_with_battery_scores(headers, '7_DAYS')
        headers.extend([
            'window_mean_words_per_entry',
            'window_entries_completed',
            'window_days_completed',
            'window_total_words',
            'window_mean_session_duration_sec'
        ])

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
            append_battery_score_values(row, rs_t1)

            stats = get_user_window_stats(user, 'PRE_T1')
            row.extend([
                stats['window_mean_words_per_entry'],
                stats['window_entries_completed'],
                stats['window_days_completed'],
                stats['window_total_words'],
                stats['window_mean_session_duration_sec']
            ])

            writer.writerow(row)

        file_name = f"1_week_assessment_export_{task.id}.csv"
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


@shared_task(time_limit=300, soft_time_limit=240)
def generate_t_first_month_export_csv(task_id):
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
            append_battery_score_values,
            extend_headers_with_battery_scores,
        )

        # 1. Fetch psychometric questions
        psy_questions = list(Question.objects.filter(questionnaire__assessment_type='PSYCHOMETRIC').order_by('order'))

        # 2. Build CSV Headers
        headers = ['ParticipantID', 'Username', 'Group', 'DateOfBirth', 'TFirstMonthStartedAt', 'TFirstMonthCompletedAt']
        item_headers, psy_columns = build_psych_item_headers_and_columns(psy_questions, '1_MONTH')
        headers.extend(item_headers)
        extend_headers_with_battery_scores(headers, '1_MONTH')
        headers.extend([
            'window_mean_words_per_entry',
            'window_entries_completed',
            'window_days_completed',
            'window_total_words',
            'window_mean_session_duration_sec'
        ])

        # 3. Fetch Users who have completed the 1_MONTH milestone psychometrics
        User = get_user_model()
        users_qs = User.objects.filter(
            is_active=True,
            response_sets__milestone='1_MONTH',
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
            rs_1m = ResponseSet.objects.filter(
                user=user,
                milestone='1_MONTH',
                questionnaire__assessment_type='PSYCHOMETRIC',
                status='COMPLETED'
            ).first()
            if not rs_1m:
                continue
            responses = Response.objects.filter(response_set=rs_1m).select_related('question', 'selected_option')
            resp_map = {r.question_id: r for r in responses}
            row = [
                user.user_id,
                user.username,
                user.group.name if user.group else 'None',
                user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else '',
                rs_1m.started_at.strftime('%Y-%m-%d %H:%M:%S') if rs_1m.started_at else '',
                rs_1m.completed_at.strftime('%Y-%m-%d %H:%M:%S') if rs_1m.completed_at else '',
            ]
            append_psych_item_values(row, resp_map, psy_columns)
            append_battery_score_values(row, rs_1m)

            stats = get_user_window_stats(user, 'PRE_T_1M')
            row.extend([
                stats['window_mean_words_per_entry'],
                stats['window_entries_completed'],
                stats['window_days_completed'],
                stats['window_total_words'],
                stats['window_mean_session_duration_sec']
            ])

            writer.writerow(row)

        file_name = f"1_month_assessment_export_{task.id}.csv"
        task.file.save(file_name, ContentFile(output.getvalue().encode('utf-8')))
        task.status = 'SUCCESS'
        task.save()
    except Exception as e:
        logger.error(f"Error generating T-First-Month export CSV for task {task_id}: {e}")
        try:
            task = ExportTask.objects.get(id=task_id)
            task.status = 'FAILED'
            task.error_message = str(e)
            task.save()
        except Exception as task_update_error:
            logger.error(f"Failed to update task {task_id} status to FAILED: {task_update_error}")
        raise e


@shared_task(time_limit=300, soft_time_limit=240)
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
            append_battery_score_values,
            extend_headers_with_battery_scores,
        )

        # 1. Fetch psychometric questions
        psy_questions = list(Question.objects.filter(questionnaire__assessment_type='PSYCHOMETRIC').order_by('order'))

        # 2. Build CSV Headers
        headers = ['ParticipantID', 'Username', 'Group', 'DateOfBirth', 'T2StartedAt', 'T2CompletedAt']
        item_headers, psy_columns = build_psych_item_headers_and_columns(psy_questions, '90_DAYS')
        headers.extend(item_headers)
        extend_headers_with_battery_scores(headers, '90_DAYS')
        headers.extend([
            'window_mean_words_per_entry',
            'window_entries_completed',
            'window_days_completed',
            'window_total_words',
            'window_mean_session_duration_sec'
        ])

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
            append_battery_score_values(row, rs_t2)

            stats = get_user_window_stats(user, 'PRE_T2')
            row.extend([
                stats['window_mean_words_per_entry'],
                stats['window_entries_completed'],
                stats['window_days_completed'],
                stats['window_total_words'],
                stats['window_mean_session_duration_sec']
            ])

            writer.writerow(row)

        file_name = f"3_month_assessment_export_{task.id}.csv"
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


@shared_task(time_limit=300, soft_time_limit=240)
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
            append_battery_score_values,
            extend_headers_with_battery_scores,
        )

        # 1. Fetch psychometric questions
        psy_questions = list(Question.objects.filter(questionnaire__assessment_type='PSYCHOMETRIC').order_by('order'))

        # 2. Build CSV Headers
        headers = ['ParticipantID', 'Username', 'Group', 'DateOfBirth', 'T3StartedAt', 'T3CompletedAt']
        item_headers, psy_columns = build_psych_item_headers_and_columns(psy_questions, '6_MONTHS')
        headers.extend(item_headers)
        extend_headers_with_battery_scores(headers, '6_MONTHS')
        headers.extend([
            'window_mean_words_per_entry',
            'window_entries_completed',
            'window_days_completed',
            'window_total_words',
            'window_mean_session_duration_sec'
        ])

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
            append_battery_score_values(row, rs_t3)

            stats = get_user_window_stats(user, 'PRE_T3')
            row.extend([
                stats['window_mean_words_per_entry'],
                stats['window_entries_completed'],
                stats['window_days_completed'],
                stats['window_total_words'],
                stats['window_mean_session_duration_sec']
            ])

            writer.writerow(row)

        file_name = f"6_month_assessment_export_{task.id}.csv"
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


@shared_task(time_limit=300, soft_time_limit=240)
def generate_t4_export_csv(task_id):
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
            append_battery_score_values,
            extend_headers_with_battery_scores,
        )

        psy_questions = list(Question.objects.filter(questionnaire__assessment_type='PSYCHOMETRIC').order_by('order'))

        headers = ['ParticipantID', 'Username', 'Group', 'DateOfBirth', 'T4StartedAt', 'T4CompletedAt']
        item_headers, psy_columns = build_psych_item_headers_and_columns(psy_questions, '1_YEAR')
        headers.extend(item_headers)
        extend_headers_with_battery_scores(headers, '1_YEAR')
        headers.extend([
            'window_mean_words_per_entry',
            'window_entries_completed',
            'window_days_completed',
            'window_total_words',
            'window_mean_session_duration_sec'
        ])

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
            append_psych_item_values(row, resp_map, psy_columns)
            append_battery_score_values(row, rs_t4)

            stats = get_user_window_stats(user, 'PRE_T4')
            row.extend([
                stats['window_mean_words_per_entry'],
                stats['window_entries_completed'],
                stats['window_days_completed'],
                stats['window_total_words'],
                stats['window_mean_session_duration_sec']
            ])

            writer.writerow(row)

        file_name = f"1_year_assessment_export_{task.id}.csv"
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


@shared_task(time_limit=300, soft_time_limit=240)
def generate_daily_entries_export_csv(task_id):
    import tempfile
    import os
    from django.core.files import File
    from activities.models import Submission
    
    try:
        task = ExportTask.objects.get(id=task_id)
        task.status = 'PROCESSING'
        task.save()
        
        headers = [
            'participant_id', 'group_id', 'window_id', 'day_number', 'entry_number',
            'entry_word_count', 'entry_text', 'entry_focus_ts', 'entry_submit_ts', 'entry_duration_sec',
            'day_total_words', 'day_entries_completed', 'day_mean_words_per_entry'
        ]
        
        submissions_qs = Submission.objects.select_related('user', 'user__group').order_by('user_id', 'activity_wave', 'experiment_day')
        
        group_name = task.filters.get('group')
        if group_name and group_name != 'All':
            submissions_qs = submissions_qs.filter(user__group__name=group_name)
            
        wave_name = task.filters.get('wave')
        if wave_name and wave_name != 'All':
            submissions_qs = submissions_qs.filter(activity_wave=wave_name)
            
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, newline='', suffix='.csv', encoding='utf-8') as temp_file:
            writer = csv.writer(temp_file, quoting=csv.QUOTE_ALL)
            writer.writerow(headers)
            
            for sub in submissions_qs.iterator(chunk_size=1000):
                e1, e2, e3 = get_submission_entries(sub)
                day_entries = [e1, e2, e3]
                day_non_empty = [e for e in day_entries if e and e.strip()]
                day_entries_completed = len(day_non_empty)
                
                day_words_list = [count_words(e) for e in day_entries]
                day_total_words = sum(day_words_list)
                day_mean_words_per_entry = (day_total_words / day_entries_completed) if day_entries_completed > 0 else 0.0
                day_mean_words_per_entry = round(day_mean_words_per_entry, 2)
                
                entries_data = [
                    (1, e1, sub.entry_1_focus_ts, sub.entry_1_submit_ts, sub.entry_1_duration_sec),
                    (2, e2, sub.entry_2_focus_ts, sub.entry_2_submit_ts, sub.entry_2_duration_sec),
                    (3, e3, sub.entry_3_focus_ts, sub.entry_3_submit_ts, sub.entry_3_duration_sec),
                ]
                
                for entry_num, text, focus_ts, submit_ts, duration in entries_data:
                    if not text or not text.strip():
                        continue
                        
                    focus_str = focus_ts.strftime('%Y-%m-%d %H:%M:%S') if focus_ts else ''
                    submit_str = submit_ts.strftime('%Y-%m-%d %H:%M:%S') if submit_ts else ''
                    
                    row = [
                        sub.user.user_id,
                        sub.user.group.name if sub.user.group else 'None',
                        sub.activity_wave,
                        sub.experiment_day or '',
                        entry_num,
                        count_words(text),
                        sanitize_csv_cell(text.replace('\n', ' ')),
                        focus_str,
                        submit_str,
                        duration or 0,
                        day_total_words,
                        day_entries_completed,
                        day_mean_words_per_entry
                    ]
                    writer.writerow(row)
                    
            temp_file_path = temp_file.name
            
        with open(temp_file_path, 'rb') as f:
            file_name = f"daily_entries_export_{task.id}.csv"
            task.file.save(file_name, File(f))
            
        task.status = 'SUCCESS'
        task.save()
        
        os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"Error generating daily entries export CSV for task {task_id}: {e}")
        try:
            task = ExportTask.objects.get(id=task_id)
            task.status = 'FAILED'
            task.error_message = str(e)
            task.save()
        except Exception as task_update_error:
            logger.error(f"Failed to update task {task_id} status to FAILED: {task_update_error}")
        raise e
