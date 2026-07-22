from app.domain.services.production.production_appointments_list_search_service import (
    ProductionAppointmentsListSearchService,
)


def test_normalize_term_empty_or_too_long() -> None:
    assert ProductionAppointmentsListSearchService.normalize_term(None) is None
    assert ProductionAppointmentsListSearchService.normalize_term("  ") is None
    assert ProductionAppointmentsListSearchService.normalize_term("x" * 81) is None


def test_appointment_row_clause_matches_operator_op_product_ct() -> None:
    clause, params = ProductionAppointmentsListSearchService.clause_for_appointment_row(
        "lind"
    )

    assert clause.startswith("(")
    assert "U.USR_NOME" in clause
    assert "SH6.H6_OP" in clause
    assert "SH6.H6_PRODUTO" in clause
    assert "SH1.H1_CTRAB" in clause
    assert all(param == "%lind%" for param in params)
    assert len(params) == 12


def test_by_op_clause_matches_op_and_product() -> None:
    clause, params = ProductionAppointmentsListSearchService.clause_for_by_op_row("2465")

    assert "SH6.H6_OP" in clause
    assert "SH6.H6_PRODUTO" in clause
    assert "U.USR_NOME" not in clause
    assert all(param == "%2465%" for param in params)
    assert len(params) == 4


def test_empty_search_returns_no_clause() -> None:
    clause, params = ProductionAppointmentsListSearchService.clause_for_appointment_row(
        None
    )
    assert clause == ""
    assert params == []
