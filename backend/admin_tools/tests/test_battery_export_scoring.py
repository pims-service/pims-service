import csv
import io

import pytest

from admin_tools.models import ExportTask
from admin_tools.tasks import generate_posttest_export_csv
from questionnaires.models import Questionnaire, Question, Option, ResponseSet, Response
from questionnaires.scoring import (
    BATTERY_EXPORT_SCORES,
    battery_score_column_names,
    calculate_scores,
)
from users.models import User


def _make_question(psy_q, order, tag):
    return Question.objects.create(
        questionnaire=psy_q,
        content=f"[{tag}] Item {order}",
        type="SCALE",
        order=order,
    )


def _make_option(question, value):
    return Option.objects.create(
        question=question,
        label=str(value),
        numeric_value=value,
        order=value,
    )


@pytest.mark.django_db
def test_calculate_scores_all_battery_scales():
    val_map = {order: 1 for order in range(1, 80)}
    val_map[11] = 2  # PERMA loneliness
    val_map[76] = 3  # SIDAS item 2 (reverse-scored)

    scores = calculate_scores(val_map)

    assert scores["PHQ9_TOTAL"] == 9
    assert scores["GAD7_TOTAL"] == 7
    assert scores["PANAS_PA"] == 4
    assert scores["PANAS_NA"] == 5
    assert scores["GRAT_GTO"] == 14
    assert scores["GRAT_GTA"] == 12
    assert scores["GRAT_TOTAL"] == 26
    # item1=1 + (10-3) + 1 + 1 + 1 = 11
    assert scores["SIDAS_TOTAL"] == 11


@pytest.mark.django_db
def test_calculate_scores_sidas_zero_when_no_ideation():
    val_map = {75: 0, 76: 5, 77: 3, 78: 2, 79: 1}
    scores = calculate_scores(val_map)
    assert scores["SIDAS_TOTAL"] == 0


@pytest.mark.django_db
def test_posttest_export_includes_all_battery_scores(admin_user, test_group):
    psy_q = Questionnaire.objects.create(
        title="Battery", assessment_type="PSYCHOMETRIC", is_active=True
    )

    questions = {}
    options = {}
    for order in range(1, 80):
        if order <= 23:
            tag = "PERMA"
        elif order <= 32:
            tag = "PHQ-9"
        elif order <= 39:
            tag = "GAD-7"
        elif order <= 48:
            tag = "PANAS"
        elif order <= 74:
            tag = "Gratitude"
        else:
            tag = "SIDAS"

        questions[order] = _make_question(psy_q, order, tag)
        value = 2 if order == 11 else (3 if order == 76 else 1)
        options[order] = _make_option(questions[order], value)

    user = User.objects.create_user(
        username="battery_export_user",
        email="battery@example.com",
        password="password",
        group=test_group,
    )

    rs = ResponseSet.objects.create(
        user=user,
        questionnaire=psy_q,
        status="COMPLETED",
        milestone="SIGNUP",
    )
    for order in range(1, 80):
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

    for col in battery_score_column_names("SIGNUP"):
        assert col in headers

    score_start = headers.index("PERMA_PositiveEmotion_SIGNUP")
    exported_scores = data_row[score_start : score_start + len(BATTERY_EXPORT_SCORES)]

    assert exported_scores[9] == "9"    # PHQ9_TOTAL
    assert exported_scores[10] == "7"   # GAD7_TOTAL
    assert exported_scores[11] == "4"   # PANAS_PA
    assert exported_scores[12] == "5"   # PANAS_NA
    assert exported_scores[13] == "14"  # GRAT_GTO
    assert exported_scores[14] == "12"  # GRAT_GTA
    assert exported_scores[15] == "26"  # GRAT_TOTAL
    assert exported_scores[16] == "11"  # SIDAS_TOTAL
