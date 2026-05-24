import pytest
from django.db import IntegrityError
from django.db import transaction
from questionnaires.models import Questionnaire, ResponseSet

@pytest.mark.django_db
def test_questionnaire_model_assessment_type_defaults(db):
    """
    Verify that a Questionnaire defaults to 'PSYCHOMETRIC' assessment_type
    and accepts the choices correctly.
    """
    # Test default
    q1 = Questionnaire.objects.create(title="Default Type Q")
    assert q1.assessment_type == 'PSYCHOMETRIC'

    # Test sociodemographic choice
    q2 = Questionnaire.objects.create(
        title="Socio Q",
        assessment_type='SOCIODEMOGRAPHIC'
    )
    assert q2.assessment_type == 'SOCIODEMOGRAPHIC'

@pytest.mark.django_db
def test_responseset_milestone_choices(db, test_user):
    """
    Verify that a ResponseSet supports milestone choice field options
    and defaults to None.
    """
    q = Questionnaire.objects.create(title="Standard Questionnaire")
    
    # Test default is None
    rs1 = ResponseSet.objects.create(
        user=test_user,
        questionnaire=q
    )
    assert rs1.milestone is None

    # Test assignment of a milestone
    rs2 = ResponseSet.objects.create(
        user=test_user,
        questionnaire=q,
        milestone='7_DAYS'
    )
    assert rs2.milestone == '7_DAYS'

@pytest.mark.django_db
def test_responseset_unique_user_questionnaire_milestone_constraint(db, test_user):
    """
    Enforce unique constraint that a user cannot submit multiple ResponseSets
    for the same Questionnaire and milestone.
    """
    q = Questionnaire.objects.create(title="Constraint Test Q")

    # Create first attempt for 3_MONTHS milestone
    ResponseSet.objects.create(
        user=test_user,
        questionnaire=q,
        milestone='3_MONTHS',
        status='COMPLETED'
    )

    # Attempt to create duplicate attempt for the same user, questionnaire, and milestone
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ResponseSet.objects.create(
                user=test_user,
                questionnaire=q,
                milestone='3_MONTHS',
                status='DRAFT'
            )

@pytest.mark.django_db
def test_responseset_unique_constraint_allows_multiple_null_milestones(db, test_user):
    """
    Verify that multiple ResponseSets with NULL milestone are permitted for the same user
    and questionnaire (standard database behavior for unique constraints with NULL).
    """
    q = Questionnaire.objects.create(title="Null Milestone Test Q")

    # Creating multiple response sets with milestone=None should succeed
    rs1 = ResponseSet.objects.create(
        user=test_user,
        questionnaire=q,
        milestone=None
    )
    rs2 = ResponseSet.objects.create(
        user=test_user,
        questionnaire=q,
        milestone=None
    )
    
    assert rs1.id is not None
    assert rs2.id is not None
    assert rs1.id != rs2.id
