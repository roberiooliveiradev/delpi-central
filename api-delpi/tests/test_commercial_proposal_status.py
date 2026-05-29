from app.domain.services.commercial_proposal_status import (
    resolve_proposal_status_category,
    resolve_proposal_status_label,
)


def test_resolve_won_status() -> None:
    assert resolve_proposal_status_label("9") == "Ganha"
    assert resolve_proposal_status_category("9") == "won"


def test_resolve_lost_status() -> None:
    assert resolve_proposal_status_label("8") == "Perdida"
    assert resolve_proposal_status_category("8") == "lost"


def test_resolve_unknown_status_falls_back_to_code() -> None:
    assert resolve_proposal_status_label("Z") == "Status Z"
    assert resolve_proposal_status_category("Z") == "other"
