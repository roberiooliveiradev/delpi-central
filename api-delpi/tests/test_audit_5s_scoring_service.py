from app.application.services.audit_5s.scoring_service import (
    CriterionScoreInput,
    calculate_overall_percentual,
    calculate_senso_percentual,
    can_attach_criterion_photo,
    is_evaluation_complete,
    is_nc_candidate,
)


def test_calculate_senso_percentual_with_na():
    scores = [
        CriterionScoreInput(senso_order=1, score=5, is_not_applicable=False),
        CriterionScoreInput(senso_order=1, score=1, is_not_applicable=False),
        CriterionScoreInput(senso_order=1, score=None, is_not_applicable=True),
    ]
    assert calculate_senso_percentual(scores) == 60.0


def test_calculate_overall_percentual():
    assert calculate_overall_percentual([80.0, 50.0, None, 100.0, 20.0]) == 62.5


def test_is_evaluation_complete():
    assert is_evaluation_complete(total_criteria=48, scored_criteria=48) is True
    assert is_evaluation_complete(total_criteria=48, scored_criteria=47) is False


def test_is_nc_candidate():
    assert is_nc_candidate(1, False) is True
    assert is_nc_candidate(3, False) is True
    assert is_nc_candidate(5, False) is False
    assert is_nc_candidate(None, True) is False


def test_can_attach_criterion_photo():
    assert can_attach_criterion_photo(1, False) is True
    assert can_attach_criterion_photo(3, False) is True
    assert can_attach_criterion_photo(5, False) is True
    assert can_attach_criterion_photo(None, True) is False
    assert can_attach_criterion_photo(None, False) is False
