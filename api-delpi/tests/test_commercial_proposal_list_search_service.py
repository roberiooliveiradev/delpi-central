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


def test_search_clause_matches_product_in_opportunity_items() -> None:
    clause, params = CommercialProposalListSearchService.clause_for_latest_row("10080055")

    assert "EXISTS (" in clause
    assert "FROM ADJ010 ADJ_S" in clause
    assert "ADJ_S.ADJ_FILIAL = AD1_FILIAL" in clause
    assert "ADJ_S.ADJ_NROPOR = AD1_NROPOR" in clause
    assert "ADJ_S.ADJ_REVISA = AD1_REVISA" in clause
    assert "ADJ_S.ADJ_PROD LIKE ?" in clause
    assert "SB1_S.B1_DESC COLLATE Latin1_General_CI_AI LIKE ?" in clause
    assert params[-2:] == ["%10080055%", "%10080055%"]


def test_search_clause_matches_status_label() -> None:
    clause, params = CommercialProposalListSearchService.clause_for_latest_row("ganha")

    assert "AD1_STATUS IN (?" in clause
    assert "9" in params


def test_search_clause_ignores_long_term() -> None:
    clause, params = CommercialProposalListSearchService.clause_for_latest_row("x" * 81)
    assert clause == ""
    assert params == []
