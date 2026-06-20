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
    # Build a val_map using the new order scheme:
    # PERMA: 1-23, PHQ-9: 25-33, GAD-7: 35-41, PANAS: 43-51,
    # Gratitude: 52-77, SIDAS: 78-82  (TEXT headers at 24, 34, 42 are excluded)
    val_map = {order: 1 for order in range(1, 83)}
    val_map[11] = 2   # PERMA loneliness
    val_map[79] = 3   # SIDAS item 2 (reverse-scored), new order 79

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
    # SIDAS item 1 (order 78) = 0 → total forced to 0 regardless of other items
    val_map = {78: 0, 79: 5, 80: 3, 81: 2, 82: 1}
    scores = calculate_scores(val_map)
    assert scores["SIDAS_TOTAL"] == 0


@pytest.mark.django_db
def test_posttest_export_includes_all_battery_scores(admin_user, test_group):
    psy_q = Questionnaire.objects.create(
        title="Battery", assessment_type="PSYCHOMETRIC", is_active=True
    )

    # New order scheme: PERMA 1-23, TEXT header @24, PHQ-9 25-33,
    # TEXT header @34, GAD-7 35-41, TEXT header @42, PANAS 43-51,
    # Gratitude 52-77, SIDAS 78-82
    TEXT_HEADER_ORDERS = {24, 34, 42}
    questions = {}
    options = {}
    for order in range(1, 83):
        if order in TEXT_HEADER_ORDERS:
            tag = "PHQ-9" if order == 24 else ("GAD-7" if order == 34 else "PANAS")
            questions[order] = Question.objects.create(
                questionnaire=psy_q,
                content=f"[{tag}] Section Header",
                type="TEXT",
                order=order,
                required=False,
            )
            # TEXT questions have no options — skip option creation
            continue

        if order <= 23:
            tag = "PERMA"
        elif order <= 33:
            tag = "PHQ-9"
        elif order <= 41:
            tag = "GAD-7"
        elif order <= 51:
            tag = "PANAS"
        elif order <= 77:
            tag = "Gratitude"
        else:
            tag = "SIDAS"

        questions[order] = _make_question(psy_q, order, tag)
        # PERMA loneliness=2, SIDAS item2 (order 79)=3, everything else=1
        value = 2 if order == 11 else (3 if order == 79 else 1)
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
    # Only create responses for SCALE questions (TEXT headers have no options)
    for order, question in questions.items():
        if question.type == "TEXT":
            continue
        Response.objects.create(
            response_set=rs,
            question=question,
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

    assert exported_scores[10] == "9"    # PHQ9_TOTAL  (PERMA_HAP now at index 8, PERMA_OVERALL at 9)
    assert exported_scores[11] == "7"   # GAD7_TOTAL
    assert exported_scores[12] == "4"   # PANAS_PA
    assert exported_scores[13] == "5"   # PANAS_NA
    assert exported_scores[14] == "14"  # GRAT_GTO
    assert exported_scores[15] == "12"  # GRAT_GTA
    assert exported_scores[16] == "26"  # GRAT_TOTAL
    assert exported_scores[17] == "11"  # SIDAS_TOTAL
