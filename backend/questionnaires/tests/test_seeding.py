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
    assert Question.objects.filter(questionnaire=socio).count() == 4

    battery = Questionnaire.objects.get(title="Longitudinal Psychometric Scales")
    assert battery.assessment_type == 'PSYCHOMETRIC'
    assert battery.is_active is True
    assert Question.objects.filter(questionnaire=battery).count() == 10

    # Verify options are correctly created for questions
    for question in Question.objects.filter(questionnaire=battery):
        assert Option.objects.filter(question=question).count() > 0

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
