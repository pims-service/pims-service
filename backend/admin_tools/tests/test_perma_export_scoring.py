import csv
import io

import pytest

from admin_tools.models import ExportTask
from admin_tools.tasks import generate_posttest_export_csv
from questionnaires.models import Questionnaire, Question, Option, ResponseSet, Response
from questionnaires.scoring import calculate_scores, perma_score_column_names
from users.models import User


@pytest.mark.django_db
def test_calculate_scores_perma_subscales():
    """PERMA subscales use item means; Lon is a single item; N is not reverse-scored."""
    val_map = {order: float(order % 10) for order in range(1, 24)}
    scores = calculate_scores(val_map)

    assert scores["PERMA_P"] == round((val_map[3] + val_map[13] + val_map[22]) / 3, 2)
    assert scores["PERMA_E"] == round((val_map[2] + val_map[10] + val_map[17]) / 3, 2)
    assert scores["PERMA_R"] == round((val_map[8] + val_map[19] + val_map[21]) / 3, 2)
    assert scores["PERMA_M"] == round((val_map[7] + val_map[9] + val_map[20]) / 3, 2)
    assert scores["PERMA_A"] == round((val_map[1] + val_map[5] + val_map[15]) / 3, 2)
    assert scores["PERMA_N"] == round((val_map[4] + val_map[14] + val_map[16]) / 3, 2)
    assert scores["PERMA_H"] == round((val_map[6] + val_map[12] + val_map[18]) / 3, 2)
    assert scores["PERMA_LON"] == val_map[11]
    overall_vals = [val_map[o] for o in [3, 13, 22, 2, 10, 17, 8, 19, 21, 7, 9, 20, 1, 5, 15, 23]]
    assert scores["PERMA_OVERALL"] == round(sum(overall_vals) / len(overall_vals), 2)


@pytest.mark.django_db
def test_posttest_export_includes_perma_scores(admin_user, test_group):
    """T0 CSV export appends computed PERMA subscale columns after item responses."""
    psy_q = Questionnaire.objects.create(
        title="Battery", assessment_type="PSYCHOMETRIC", is_active=True
    )

    questions = {}
    for order in range(1, 24):
        questions[order] = Question.objects.create(
            questionnaire=psy_q,
            content=f"[PERMA] Item {order}",
            type="SCALE",
            order=order,
        )

    options = {}
    for order, question in questions.items():
        value = 2 if order == 11 else 5
        options[order] = Option.objects.create(
            question=question,
            label=str(value),
            numeric_value=value,
            order=value,
        )

    user = User.objects.create_user(
        username="perma_export_user",
        email="perma@example.com",
        password="password",
        group=test_group,
    )

    rs = ResponseSet.objects.create(
        user=user,
        questionnaire=psy_q,
        status="COMPLETED",
        milestone="SIGNUP",
    )
    for order in range(1, 24):
        Response.objects.create(
            response_set=rs,
            question=questions[order],
            selected_option=options[order],
        )

    task = ExportTask.objects.create(user=admin_user, filters={"group": "All"})
    generate_posttest_export_csv(task.id)

    task.refresh_from_db()
    assert task.status == "SUCCESS"

    reader = csv.reader(io.StringIO(task.file.read().decode("utf-8")))
    headers, data_row = next(reader), next(reader)

    for col in perma_score_column_names("SIGNUP"):
        assert col in headers

    score_start = headers.index("PERMA_PositiveEmotion_SIGNUP")
    exported_scores = data_row[score_start : score_start + 9]

    assert exported_scores[0] == "5.0"  # P
    assert exported_scores[1] == "5.0"  # E
    assert exported_scores[2] == "5.0"  # R
    assert exported_scores[3] == "5.0"  # M
    assert exported_scores[4] == "5.0"  # A
    assert exported_scores[5] == "5.0"  # N
    assert exported_scores[6] == "5.0"  # H
    assert exported_scores[7] == "2.0"  # Lon
    assert exported_scores[8] == "5.0"  # Overall
