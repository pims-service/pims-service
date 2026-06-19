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
