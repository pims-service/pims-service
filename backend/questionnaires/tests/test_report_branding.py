from questionnaires.tasks import MILESTONE_FILENAME, _load_logo_base64


def test_report_logo_is_found():
    # The institute seal must still load after the PIMS -> Psycheversity rename of file names.
    assert _load_logo_base64()


def test_report_filenames_use_psycheversity():
    assert all(name.startswith('psycheversity_') for name in MILESTONE_FILENAME.values())
