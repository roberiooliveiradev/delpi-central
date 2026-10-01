"""PERF-002 — data de filtro fornecida mas inválida não pode remover predicado SQL.

Semântica alvo:
  ausente   (None/"") → predicado opcional ausente (comportamento preservado)
  válida              → mesmo valor Protheus/predicado de antes
  fornecida inválida  → InvalidProtheusDateError (nunca vira ausente)
"""

from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.persistence.totvs.query_builder import (
    InvalidProtheusDateError,
    QueryBuilder,
)


# ----------------------------------------------------------
# convert_date_to_protheus — ausente vs inválido
# ----------------------------------------------------------


def test_convert_date_absent_values_still_return_none() -> None:
    assert QueryBuilder().convert_date_to_protheus(None) is None
    assert QueryBuilder().convert_date_to_protheus("") is None
    assert QueryBuilder().convert_date_to_protheus("   ") is None


def test_blank_param_is_contractually_absent() -> None:
    """Contrato DELPI: ?start_date= equivale a ausência (ver test_period_query_params).

    resolve_period_dates normaliza "" e "  " para None na borda HTTP antes
    do DTO; aqui provamos que blank direto no builder produz o mesmo
    resultado de None — sem predicado, sem exceção. Não viola
    RQ-PERF002-06: RQ distingue ausência semântica de data malformada,
    e blank é definido como ausência pelo contrato canônico.
    """
    from app.interface.http.period_query_params import resolve_period_dates

    assert resolve_period_dates(start_date="", end_date="") == (None, None)

    qb_omitted = QueryBuilder()
    qb_omitted.date_range("F", None, None)

    qb_blank = QueryBuilder()
    qb_blank.date_range("F", "", "  ")

    assert qb_blank.build() == qb_omitted.build() == ("1=1", ())


def test_convert_date_preserves_valid_semantics() -> None:
    qb = QueryBuilder()
    assert qb.convert_date_to_protheus("01-10-2026") == "20261001"
    assert qb.convert_date_to_protheus("2026-10-01") == "20261001"
    assert qb.convert_date_to_protheus("01/10/2026") == "20261001"
    assert qb.convert_date_to_protheus("20261001") == "20261001"
    assert qb.convert_date_to_protheus(datetime(2026, 10, 1)) == "20261001"
    assert qb.convert_date_to_protheus(date(2026, 10, 1)) == "20261001"


def test_convert_date_rejects_provided_invalid_values() -> None:
    qb = QueryBuilder()
    for invalid in ("01-10-202", "01-10-20", "01-10-2", "garbage"):
        with pytest.raises(InvalidProtheusDateError, match="inválida"):
            qb.convert_date_to_protheus(invalid)


def test_convert_date_rejects_non_string_non_date() -> None:
    with pytest.raises(InvalidProtheusDateError):
        QueryBuilder().convert_date_to_protheus(object())


# ----------------------------------------------------------
# date_range — predicado nunca é removido por data inválida
# ----------------------------------------------------------


def test_date_range_absent_bounds_remain_optional() -> None:
    qb = QueryBuilder()
    qb.date_range("D2_EMISSAO", None, None)
    assert qb.build() == ("1=1", ())


def test_date_range_absent_start_keeps_upper_bound_only() -> None:
    qb = QueryBuilder()
    qb.date_range("D2_EMISSAO", None, "31-10-2026")
    assert qb.build() == ("D2_EMISSAO <= ?", ("20261031",))


def test_date_range_absent_end_keeps_lower_bound_only() -> None:
    qb = QueryBuilder()
    qb.date_range("D2_EMISSAO", "01-10-2026", None)
    assert qb.build() == ("D2_EMISSAO >= ?", ("20261001",))


def test_date_range_valid_bounds_produce_same_between_sql() -> None:
    qb = QueryBuilder()
    qb.date_range("D2_EMISSAO", "01-10-2026", "31-10-2026")
    assert qb.build() == (
        "D2_EMISSAO BETWEEN ? AND ?",
        ("20261001", "20261031"),
    )


def test_date_range_invalid_start_raises_instead_of_dropping_bound() -> None:
    qb = QueryBuilder()
    with pytest.raises(InvalidProtheusDateError):
        qb.date_range("D2_EMISSAO", "01-10-202", "31-10-2026")
    assert qb.build() == ("1=1", ())  # nenhum predicado parcial gravado


def test_date_range_invalid_end_raises_instead_of_dropping_bound() -> None:
    qb = QueryBuilder()
    with pytest.raises(InvalidProtheusDateError):
        qb.date_range("D2_EMISSAO", "01-10-2026", "31-10-202")
    assert qb.build() == ("1=1", ())


# ----------------------------------------------------------
# HTTP boundary — rota representativa deve responder 4xx
# ----------------------------------------------------------


def _superadmin_user():
    return SimpleNamespace(is_superadmin=True, rbac_unavailable=False)


def _lmp_use_case_running_real_date_range():
    """Stub que executa o date_range real com os campos do DTO."""
    use_case = MagicMock()

    def _execute_summary(dto, *, status_filter=None, summary_mode="kpi"):
        QueryBuilder().date_range("TEST_FIELD", dto.date_start, dto.date_end)
        return {"total": 0}

    use_case.execute_summary.side_effect = _execute_summary
    return use_case


def _call_lmp_summary_route(**params):
    from app.interface.http.routes.engineering.engineering_router import (
        lmps_dashboard_summary_route,
    )

    with (
        patch(
            "delpi_auth.authorization.resolve_user_context",
            return_value=_superadmin_user(),
        ),
        patch(
            "app.interface.http.routes.engineering.engineering_router."
            "build_engineering_list_lmps_dashboard_use_case",
            return_value=_lmp_use_case_running_real_date_range(),
        ),
        patch(
            "app.interface.http.routes.engineering.engineering_router."
            "enrich_dashboard_metric",
            side_effect=lambda summary, **_: summary,
        ),
    ):
        return lmps_dashboard_summary_route(**params)


def test_lmp_summary_route_returns_400_for_malformed_start_date() -> None:
    response = _call_lmp_summary_route(start_date="01-10-202", end_date="31-10-2026")
    assert response.status_code == 400
    import json

    body = json.loads(response.body)
    assert body["success"] is False


def test_lmp_summary_route_valid_dates_keep_success() -> None:
    response = _call_lmp_summary_route(start_date="01-10-2026", end_date="31-10-2026")
    import json

    body = json.loads(response.body)
    assert response.status_code == 200
    assert body["success"] is True


def test_lmp_summary_route_blank_dates_equal_omitted() -> None:
    """?start_date= (blank) é ausência contratual — mesmo sucesso que omitido."""
    blank = _call_lmp_summary_route(start_date="", end_date="")
    omitted = _call_lmp_summary_route()
    import json

    for response in (blank, omitted):
        assert response.status_code == 200
        assert json.loads(response.body)["success"] is True
