import pytest
from questionnaires.models import Questionnaire, QuestionnaireResponse

@pytest.mark.django_db
def test_questionnaire_creation():
    q = Questionnaire.objects.create(
        title="Pre-Exp Survey",
        q_type='pre',
        description="Initial assessment"
    )
    assert q.title == "Pre-Exp Survey"
    assert str(q) == "Pre-Experiment - Pre-Exp Survey"

@pytest.mark.django_db
def test_response_creation(test_user):
    q = Questionnaire.objects.create(title="Survey", q_type='daily')
    res = QuestionnaireResponse.objects.create(
        user=test_user,
        questionnaire=q,
        responses={"q1": "Answer 1"}
    )
    assert res.responses["q1"] == "Answer 1"
