"""Testes SQL — carga máquina (SH8010 alocada + apontamento HZA010)."""

from __future__ import annotations

import pytest

from app.domain.production.machine_load_scope import (
    MACHINE_LOAD_ALLOCATION_TABLE,
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


def test_window_filter_uses_h8_dtini() -> None:
    query, params = sql.build_operations_count_query(**_filters(branch=None))
    assert "OA.H8_DTINI >= ?" in query
    assert "OA.H8_DTINI <= ?" in query
    assert "OA.H8_FILIAL IN (?, ?)" in query
    assert params == (*_JOIN_PARAMS, "20260819", "20260826", "01", "02")


def test_running_operations_survive_the_scheduled_window() -> None:
    """A alocação atrasa, mas a máquina rodando precisa aparecer na fila."""
    query, _ = sql.build_operations_count_query(**_filters())
    assert "OR CASE WHEN ISNULL(AP.active_count, 0) > 0 THEN 1 ELSE 0 END = 1" in query


def test_pa_due_date_comes_from_mother_order() -> None:
    """A entrega do PA é a da OP mãe (sequência 001), não a da OP filha."""
    query, _ = sql.build_operations_query(**_filters(), offset=0, page_size=10)
    assert "PA.OP_CHAVE = LEFT(OA.H8_OP, 8) + '001'" in query
    assert "PA.DT_ENTREGA AS pa_due_date" in query


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
        "%24640401002%",
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
    assert "ORDER BY CASE WHEN ISNULL(AP.active_count, 0) > 0 THEN 1 ELSE 0 END DESC" in query
    assert "OA.H8_DTINI ASC, OA.H8_HRINI ASC" in query


def test_invalid_sort_is_rejected() -> None:
    with pytest.raises(ValueError):
        sql.build_operations_query(**_filters(), sort="bogus", offset=0, page_size=10)


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
