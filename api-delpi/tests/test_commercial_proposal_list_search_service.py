from app.domain.services.commercial_proposal_list_search_service import (
    CommercialProposalListSearchService,
)


def test_search_clause_empty_when_term_missing() -> None:
    clause, params = CommercialProposalListSearchService.clause_for_latest_row(None)
    assert clause == ""
    assert params == []


def test_search_clause_matches_text_fields() -> None:
    clause, params = CommercialProposalListSearchService.clause_for_latest_row("weg")

    assert clause.startswith("AND (")
    assert "AD1_DESCRI COLLATE Latin1_General_CI_AI LIKE ?" in clause
    assert "AD1_NROPOR LIKE ?" in clause
    assert all(param == "%weg%" for param in params[:8])


def test_search_clause_matches_status_label() -> None:
    clause, params = CommercialProposalListSearchService.clause_for_latest_row("ganha")

    assert "AD1_STATUS IN (?" in clause
    assert "9" in params


def test_search_clause_ignores_long_term() -> None:
    clause, params = CommercialProposalListSearchService.clause_for_latest_row("x" * 81)
    assert clause == ""
    assert params == []
