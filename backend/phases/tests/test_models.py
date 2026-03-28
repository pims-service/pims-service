import pytest
from phases.models import Phase
from datetime import date, timedelta

@pytest.mark.django_db
def test_phase_creation():
    phase = Phase.objects.create(
        phase_number=2,
        name="Phase 2",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=7)
    )
    assert phase.phase_number == 2
    assert str(phase) == "Phase 2: Phase 2"
