import pytest
from django.core.management import call_command
from questionnaires.models import Questionnaire, Question, Option

@pytest.mark.django_db
def test_seed_longitudinal_scales_command_success(db):
    """
    Ensure the seed command runs successfully, creates the two required
    questionnaires, and populates questions and options correctly.
    """
    # Verify pre-seed state is empty
    assert Questionnaire.objects.count() == 0

    # Run the seed command
    call_command('seed_longitudinal_scales')

    # Verify both questionnaires exist
    assert Questionnaire.objects.count() == 2
    
    socio = Questionnaire.objects.get(title="Sociodemographic Survey")
    assert socio.assessment_type == 'SOCIODEMOGRAPHIC'
    assert socio.is_active is True
    assert Question.objects.filter(questionnaire=socio).count() == 12

    battery = Questionnaire.objects.get(title="Longitudinal Psychometric Scales")
    assert battery.assessment_type == 'PSYCHOMETRIC'
    assert battery.is_active is True
    assert Question.objects.filter(questionnaire=battery).count() == 82

    # Verify options are correctly created for scored questions (skip TEXT headers)
    for question in Question.objects.filter(questionnaire=battery):
        if question.type != 'TEXT':
            assert Option.objects.filter(question=question).count() > 0

    # Verify sequence order of scales in the battery
    questions = Question.objects.filter(questionnaire=battery).order_by('order')
    scale_order = []
    for q in questions:
        # extract scale group from content prefix e.g. [PERMA] -> PERMA
        if q.content.startswith('[') and ']' in q.content:
            group = q.content[1:q.content.index(']')]
            if not scale_order or scale_order[-1] != group:
                scale_order.append(group)
    assert scale_order == ['PERMA', 'PHQ-9', 'GAD-7', 'PANAS', 'Gratitude', 'SIDAS']

    # Verify exact option counts — guards against stale options from scale reassignment
    # PERMA (0-10): 11 options each; PHQ-9 / GAD-7 (0-3): 4 each;
    # PANAS (0-4): 5 each; Gratitude (0-4): 5 each; SIDAS (0-10): 11 each
    scale_expected_options = {
        'PERMA': 11, 'PHQ-9': 4, 'GAD-7': 4, 'PANAS': 5, 'Gratitude': 5, 'SIDAS': 11,
    }
    for q in questions:
        if q.type == 'TEXT':
            continue
        if q.content.startswith('[') and ']' in q.content:
            group = q.content[1:q.content.index(']')]
            expected = scale_expected_options.get(group)
            if expected is not None:
                actual = Option.objects.filter(question=q).count()
                assert actual == expected, (
                    f"Question order={q.order} [{group}] has {actual} options, expected {expected}. "
                    "Stale options from a prior scale reassignment may not have been pruned."
                )

@pytest.mark.django_db
def test_seed_prunes_stale_options_on_reseed(db):
    """
    Regression: Gratitude items 24-26 (orders 75-77) previously inherited 0-10
    SIDAS options after an order-shift migration. Re-seeding must prune the extra
    options so each Gratitude question ends up with exactly 5 options (0-4).
    """
    from questionnaires.models import Option as Opt

    call_command('seed_longitudinal_scales')

    battery = Questionnaire.objects.get(title="Longitudinal Psychometric Scales")

    # Manually inject stale 0-10 SIDAS-style options onto Gratitude items 24-26
    # (orders 75, 76, 77) to reproduce the bug.
    grat_tail_orders = [75, 76, 77]
    for order in grat_tail_orders:
        q = Question.objects.get(questionnaire=battery, order=order)
        for v in range(5, 11):  # values 5-10 are stale
            Opt.objects.get_or_create(question=q, numeric_value=v, defaults={"label": str(v), "order": v})
        assert Opt.objects.filter(question=q).count() == 11  # 0-10 = bug state

    # Re-seeding must prune the stale options back to exactly 5 (0-4)
    call_command('seed_longitudinal_scales')
    for order in grat_tail_orders:
        q = Question.objects.get(questionnaire=battery, order=order)
        actual = Opt.objects.filter(question=q).count()
        assert actual == 5, (
            f"Gratitude order={order} still has {actual} options after reseed; expected 5 (0-4)."
        )


@pytest.mark.django_db
def test_seed_longitudinal_scales_is_idempotent(db):
    """
    Verify that calling the seed command multiple times does not result
    in duplicate questionnaires, questions, or options.
    """
    # Call command first time
    call_command('seed_longitudinal_scales')
    assert Questionnaire.objects.count() == 2
    q_count_1 = Question.objects.count()
    o_count_1 = Option.objects.count()

    # Call command second time
    call_command('seed_longitudinal_scales')
    assert Questionnaire.objects.count() == 2
    assert Question.objects.count() == q_count_1
    assert Option.objects.count() == o_count_1
