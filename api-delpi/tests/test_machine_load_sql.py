"""Testes SQL — carga máquina (SH8010 alocada + apontamento HZA010)."""

from __future__ import annotations

import pytest

from app.domain.production.machine_load_scope import (
    MACHINE_LOAD_ALLOCATION_TABLE,
    MACHINE_LOAD_ORDER_TABLE,
    MACHINE_LOAD_ORDERS_VIEW,
    MACHINE_LOAD_ROUTING_TABLE,
    MACHINE_LOAD_WORK_CENTER_TABLE,
    SORT_VALUES,
)
from app.domain.totvs.protheus_operation_appointments import (
    OPERATION_APPOINTMENT_TABLE,
)
from app.domain.totvs.protheus_users import PROTHEUS_USER_TABLE
from app.infrastructure.persistence.totvs.production import machine_load_sql as sql

_ACTIVE_SINCE = "20260817"
_HISTORY_SINCE = "20260720"

# Os parâmetros do FROM vêm antes dos do WHERE porque o LEFT JOIN da HZA aparece
# antes na query.
_JOIN_PARAMS = (_ACTIVE_SINCE, _HISTORY_SINCE)


def _filters(**overrides):
    base = {
        "scheduled_start": "20260819",
        "scheduled_end": "20260826",
        "branch": "01",
        "appointment_active_since": _ACTIVE_SINCE,
        "appointment_history_since": _HISTORY_SINCE,
    }
    base.update(overrides)
    return base


def test_work_centers_query_joins_and_groups_by_work_center() -> None:
    query, params = sql.build_work_centers_query(**_filters())
    assert MACHINE_LOAD_ALLOCATION_TABLE in query
    assert MACHINE_LOAD_WORK_CENTER_TABLE in query
    assert MACHINE_LOAD_ROUTING_TABLE in query
    assert MACHINE_LOAD_ORDERS_VIEW in query
    assert query.count("WITH (NOLOCK)") >= 5
    assert "GROUP BY LTRIM(RTRIM(OA.H8_CTRAB))" in query
    assert params == (*_JOIN_PARAMS, "20260819", "20260826", "01")


def test_base_query_excludes_deleted_rows_in_every_table() -> None:
    query, _ = sql.build_work_centers_query(**_filters())
    for alias in ("OA", "OP", "P", "HB", "G2", "Z"):
        assert f"{alias}.D_E_L_E_T_ = ''" in query


def test_open_only_defaults_to_open_orders() -> None:
    query, _ = sql.build_operations_count_query(**_filters())
    assert "OP.C2_QUANT > OP.C2_QUJE" in query


def test_open_only_false_returns_closed_orders() -> None:
    query, _ = sql.build_operations_count_query(**_filters(open_only=False))
    assert "OP.C2_QUANT <= OP.C2_QUJE" in query


def test_open_only_none_skips_open_closed_filter() -> None:
    query, _ = sql.build_operations_count_query(**_filters(open_only=None))
    assert "OP.C2_QUANT > OP.C2_QUJE" not in query
    assert "OP.C2_QUANT <= OP.C2_QUJE" not in query


def test_production_order_filter_uses_prefix_like() -> None:
    query, params = sql.build_operations_count_query(
        **_filters(production_order="108404")
    )
    assert "LTRIM(RTRIM(OA.H8_OP)) LIKE ?" in query
    assert "108404%" in params
    assert "%108404%" not in params


def test_window_filter_uses_h8_dtini() -> None:
    query, params = sql.build_operations_count_query(**_filters(branch=None))
    assert "OA.H8_DTINI >= ?" in query
    assert "OA.H8_DTINI <= ?" in query
    assert "OA.H8_FILIAL IN (?, ?)" in query
    assert params == (*_JOIN_PARAMS, "20260819", "20260826", "01", "02")


def test_running_operations_survive_the_scheduled_window() -> None:
    """A alocação atrasa, mas a máquina rodando precisa aparecer na fila."""
    query, _ = sql.build_operations_count_query(**_filters())
    assert f"OR {sql._IN_PRODUCTION_EXPR} = 1" in query


def test_pa_due_date_comes_from_mother_order() -> None:
    """A entrega do PA é a da OP mãe (sequência 001), não a da OP filha."""
    query, _ = sql.build_operations_query(**_filters(), offset=0, page_size=10)
    assert "PA.OP_CHAVE = LEFT(OA.H8_OP, 8) + '001'" in query
    assert "PA.DT_ENTREGA AS pa_due_date" in query


def test_delivery_window_replaces_the_scheduled_window() -> None:
    """O PCP planeja por entrega: com delivery_*, a programação não recorta mais."""
    query, params = sql.build_operations_count_query(
        **_filters(delivery_start="2026-08-01", delivery_end="2026-09-03")
    )
    assert "OA.H8_DTINI >= ?" not in query
    assert f"{sql.DUE_DATE_EXPR} >= ?" in query
    assert f"{sql.DUE_DATE_EXPR} <= ?" in query
    assert params == (*_JOIN_PARAMS, "2026-08-01", "2026-09-03", "01")


def test_delivery_window_accepts_an_open_start() -> None:
    """Sem início, tudo que está atrasado continua na fila."""
    query, params = sql.build_operations_count_query(**_filters(delivery_end="2026-09-03"))
    assert f"{sql.DUE_DATE_EXPR} >= ?" not in query
    assert f"{sql.DUE_DATE_EXPR} <= ?" in query
    assert params == (*_JOIN_PARAMS, "2026-09-03", "01")


def test_running_operations_survive_the_delivery_window() -> None:
    query, _ = sql.build_operations_count_query(**_filters(delivery_end="2026-09-03"))
    assert f"OR {sql._IN_PRODUCTION_EXPR} = 1" in query


def test_effective_due_date_falls_back_to_the_order_forecast() -> None:
    """Sem OP mãe na view PCP, a previsão da própria OP evita operação sem entrega."""
    query, _ = sql.build_operations_query(**_filters(), offset=0, page_size=10)
    assert "COALESCE(PA.DT_ENTREGA, TRY_CONVERT(DATE," in query
    assert "OP.C2_DATPRF" in query
    assert "AS due_date" in query
    assert "AS due_date_source" in query


def test_work_centers_query_exposes_delivery_bounds() -> None:
    query, _ = sql.build_work_centers_query(**_filters())
    assert "AS first_due_date" in query
    assert "AS last_due_date" in query
    assert "AS missing_due_date_count" in query


def test_appointment_join_matches_branch_order_and_operation() -> None:
    query, _ = sql.build_operations_query(**_filters(), offset=0, page_size=10)
    assert OPERATION_APPOINTMENT_TABLE in query
    assert "AP.ap_branch = OA.H8_FILIAL" in query
    assert "AP.ap_order = OA.H8_OP" in query
    assert "AP.ap_operation = OA.H8_OPER" in query


def test_only_open_and_recent_appointments_count_as_running() -> None:
    """Status 2 e 3 já encerraram; aberto antigo é apontamento esquecido."""
    query, _ = sql.build_operations_query(**_filters(), offset=0, page_size=10)
    assert "Z.HZA_STATUS = '1'" in query
    assert "LTRIM(RTRIM(ISNULL(Z.HZA_DTFIM, ''))) = ''" in query
    assert "AND Z.HZA_DTINI >= ?" in query


def test_operator_name_is_resolved_inside_the_appointment_aggregate() -> None:
    """Resolver SYS_USR contra a SH8 inteira levava mais de um minuto."""
    query, _ = sql.build_operations_query(**_filters(), offset=0, page_size=10)
    assert PROTHEUS_USER_TABLE in query
    assert query.index(PROTHEUS_USER_TABLE) < query.index("GROUP BY A.ap_branch")
    assert "USR.USR_ID)) = LTRIM(RTRIM(Z.HZA_OPERAD))" in query


def test_appointment_status_query_skips_sh8() -> None:
    query, params = sql.build_appointment_status_query(
        branch="02",
        appointment_active_since=_ACTIVE_SINCE,
        appointment_history_since=_HISTORY_SINCE,
    )
    assert OPERATION_APPOINTMENT_TABLE in query
    assert MACHINE_LOAD_ALLOCATION_TABLE not in query
    assert PROTHEUS_USER_TABLE in query
    assert params == (_ACTIVE_SINCE, "02", _HISTORY_SINCE)
    assert "GROUP BY A.ap_branch, A.ap_order, A.ap_operation" in query


def test_work_centers_query_counts_operations_in_production() -> None:
    query, _ = sql.build_work_centers_query(**_filters())
    assert "AS in_production_count" in query


def test_operations_query_exposes_contract_columns() -> None:
    query, _ = sql.build_operations_query(**_filters(), offset=0, page_size=10)
    for column in (
        "AS work_center",
        "AS work_center_name",
        "AS production_order",
        "AS operation_description",
        "AS tool",
        "AS product_code",
        "AS product_description",
        "AS planned_qty",
        "AS pending_qty",
        "AS pa_due_date",
        "AS active_appointment_count",
        "AS active_marker",
        "AS last_marker",
        "AS appointment_count",
        "AS last_appointment_date",
    ):
        assert column in query
    # A quantidade vem da SC2010: H8_QUANT sempre chega 1 na SH8 da Delpi.
    assert "OA.H8_QUANT" not in query


def test_operations_query_pagination_params_are_last() -> None:
    query, params = sql.build_operations_query(
        **_filters(work_center="CT-02"), offset=20, page_size=50
    )
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in query
    assert params == (*_JOIN_PARAMS, "20260819", "20260826", "01", "CT-02", 20, 50)


def test_optional_filters_append_params_in_order() -> None:
    _, params = sql.build_operations_count_query(
        **_filters(
            work_center="CT-02",
            product_code="9026",
            production_order="24640401002",
            tool="23-B31",
        )
    )
    assert params == (
        *_JOIN_PARAMS,
        "20260819",
        "20260826",
        "01",
        "CT-02",
        "%9026%",
        "24640401002%",
        "23-B31",
    )


@pytest.mark.parametrize("sort", SORT_VALUES)
def test_every_sort_value_builds_order_by(sort: str) -> None:
    query, _ = sql.build_operations_query(
        **_filters(), sort=sort, offset=0, page_size=10
    )
    assert "ORDER BY" in query


def test_default_sort_puts_running_operations_first() -> None:
    query, _ = sql.build_operations_query(**_filters(), offset=0, page_size=10)
    assert "ORDER BY CASE WHEN ISNULL(AP.active_count, 0) > 0" in query
    assert "OA.H8_DTINI ASC, OA.H8_HRINI ASC" in query


def test_in_production_expression_ignores_finished_orders() -> None:
    """Apontamento aberto de OP encerrada não pode contar como rodando."""
    query, _ = sql.build_operations_query(**_filters(), offset=0, page_size=10)
    assert (
        "CASE WHEN ISNULL(AP.active_count, 0) > 0 AND NOT (OP.C2_DATRF IS NOT NULL"
        " AND LTRIM(RTRIM(OP.C2_DATRF)) <> '') THEN 1 ELSE 0 END" in query
    )


def test_operations_query_exposes_order_finish_columns() -> None:
    query, _ = sql.build_operations_query(**_filters(), offset=0, page_size=10)
    assert "AS order_is_finished" in query
    assert "AS order_finish_date" in query


def test_invalid_sort_is_rejected() -> None:
    with pytest.raises(ValueError):
        sql.build_operations_query(**_filters(), sort="bogus", offset=0, page_size=10)


def test_order_finish_flags_query_uses_c2_datrf() -> None:
    built = sql.build_order_finish_flags_query(
        branch="01", production_orders=["10846301001", "10846301001", ""]
    )
    assert built is not None
    query, params = built
    assert "C2_DATRF" in query
    assert MACHINE_LOAD_ORDER_TABLE in query
    assert params == ("01", "10846301001")
