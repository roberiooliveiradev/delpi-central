"""Testes — mapper e janela da carga máquina."""

from __future__ import annotations

from datetime import date

import pytest

from app.application.dto.production.machine_load_request import (
    MachineLoadOperationsRequest,
    MachineLoadWindow,
)
from app.domain.services.production.machine_load_operation_mapper import (
    MachineLoadOperationMapper,
)
from app.domain.totvs.protheus_operation_appointments import (
    PRODUCTION_STATUS_IN_PROGRESS,
    PRODUCTION_STATUS_NOT_STARTED,
    PRODUCTION_STATUS_STARTED,
)

# HZA_DTINI (8) + HZA_HRINI (8) + HZA_OPERAD (6) + nome do operador.
_ACTIVE_MARKER = "2026081918:58:25000223SILVANA ANDRADE DOS SANTOS"

_ROW = {
    "branch": "01",
    "work_center": "CT-02",
    "work_center_name": "APLICAÇÃO DE TERMINAIS",
    "scheduled_date": "20260820",
    "scheduled_start_time": "05:00",
    "scheduled_end_date": "20260820",
    "scheduled_end_time": "05:52",
    "production_order": "24640401002",
    "operation_code": "03",
    "operation_description": "CORTAR E APLICAR 10080059 E 10080568",
    "tool": "23-B31",
    "resource": "CT-02",
    "product_code": "50320064",
    "product_description": "CF1,5BRAN-00148/06/05-5900-6800",
    "unit": "MI",
    "planned_qty": 7.1,
    "produced_qty": 1.1,
    "pending_qty": 6.0,
    "pa_due_date": "2026-08-21",
    "pa_production_order": "24640401001",
    "pa_product_code": "90300080",
    "pa_product_description": "CHICOTE DE LIGAÇÃO",
}


def test_map_operation_converts_protheus_dates_to_iso() -> None:
    item = MachineLoadOperationMapper.map_operation(_ROW)
    assert item["scheduled_date"] == "2026-08-20"
    assert item["scheduled_end_date"] == "2026-08-20"
    assert item["pa_due_date"] == "2026-08-21"


def test_map_operation_keeps_full_production_order_and_tool() -> None:
    item = MachineLoadOperationMapper.map_operation(_ROW)
    assert item["production_order"] == "24640401002"
    assert item["tool"] == "23-B31"
    assert item["is_manual_operation"] is False
    assert item["operation_description"] == "CORTAR E APLICAR 10080059 E 10080568"


def test_manual_labor_tool_is_flagged() -> None:
    item = MachineLoadOperationMapper.map_operation({**_ROW, "tool": "MOD"})
    assert item["is_manual_operation"] is True


def test_pending_qty_falls_back_to_planned_minus_produced() -> None:
    item = MachineLoadOperationMapper.map_operation({**_ROW, "pending_qty": None})
    assert item["pending_qty"] == 6.0


def test_empty_protheus_date_becomes_none() -> None:
    item = MachineLoadOperationMapper.map_operation(
        {**_ROW, "scheduled_end_date": "00000000", "pa_due_date": ""}
    )
    assert item["scheduled_end_date"] is None
    assert item["pa_due_date"] is None


def test_operation_without_appointment_is_not_started() -> None:
    item = MachineLoadOperationMapper.map_operation(_ROW)
    assert item["production_status"] == PRODUCTION_STATUS_NOT_STARTED
    assert item["is_in_production"] is False
    assert item["active_operator_name"] is None
    assert item["production_started_date"] is None


def test_open_appointment_marks_operation_in_production_with_operator() -> None:
    item = MachineLoadOperationMapper.map_operation(
        {
            **_ROW,
            "active_appointment_count": 1,
            "active_operator_count": 1,
            "appointment_count": 3,
            "active_marker": _ACTIVE_MARKER,
            "last_appointment_date": "20260819",
        }
    )
    assert item["production_status"] == PRODUCTION_STATUS_IN_PROGRESS
    assert item["is_in_production"] is True
    assert item["active_operator_name"] == "SILVANA ANDRADE DOS SANTOS"
    assert item["active_operator_code"] == "000223"
    assert item["production_started_date"] == "2026-08-19"
    assert item["production_started_time"] == "18:58:25"
    assert item["last_appointment_date"] == "2026-08-19"


def test_closed_appointment_means_started_but_not_running() -> None:
    """Status 2 e 3 encerram o apontamento: a operação já passou pela máquina."""
    item = MachineLoadOperationMapper.map_operation(
        {
            **_ROW,
            "active_appointment_count": 0,
            "appointment_count": 2,
            "active_marker": "",
            "last_marker": _ACTIVE_MARKER,
            "last_appointment_date": "20260818",
        }
    )
    assert item["production_status"] == PRODUCTION_STATUS_STARTED
    assert item["is_in_production"] is False
    assert item["active_operator_name"] == "SILVANA ANDRADE DOS SANTOS"
    assert item["active_operator_code"] == "000223"
    assert item["last_appointment_date"] == "2026-08-18"


def test_finished_order_without_hza_history_is_started() -> None:
    item = MachineLoadOperationMapper.map_operation(
        {
            **_ROW,
            "active_appointment_count": 0,
            "appointment_count": 0,
            "order_is_finished": 1,
            "order_finish_date": "20260815",
        }
    )
    assert item["production_status"] == PRODUCTION_STATUS_STARTED
    assert item["is_in_production"] is False
    assert item["production_started_date"] == "2026-08-15"


def test_finished_order_overrides_open_appointment() -> None:
    """Coletor esquecido aberto: OP encerrada volta a «Já apontada»."""
    item = MachineLoadOperationMapper.map_operation(
        {
            **_ROW,
            "active_appointment_count": 1,
            "active_operator_count": 1,
            "appointment_count": 3,
            "active_marker": _ACTIVE_MARKER,
            "last_marker": _ACTIVE_MARKER,
            "order_is_finished": 1,
            "order_finish_date": "20260819",
        }
    )
    assert item["production_status"] == PRODUCTION_STATUS_STARTED
    assert item["is_in_production"] is False
    assert item["active_operator_count"] == 0
    assert item["active_operator_name"] == "SILVANA ANDRADE DOS SANTOS"


def test_zero_pending_overrides_open_appointment() -> None:
    """Saldo da OP zerado: cronômetro aberto no coletor não mantém «Em produção»."""
    item = MachineLoadOperationMapper.map_operation(
        {
            **_ROW,
            "pending_qty": 0,
            "produced_qty": 7.1,
            "active_appointment_count": 1,
            "active_operator_count": 1,
            "appointment_count": 2,
            "active_marker": _ACTIVE_MARKER,
            "last_marker": _ACTIVE_MARKER,
        }
    )
    assert item["production_status"] == PRODUCTION_STATUS_STARTED
    assert item["is_in_production"] is False
    assert item["active_operator_count"] == 0
    assert item["active_operator_name"] == "SILVANA ANDRADE DOS SANTOS"


def test_missing_pending_qty_does_not_invent_exhausted_balance() -> None:
    """Enrich HZA sem saldo SC2: ausência do campo ≠ saldo zero."""
    row = {
        "branch": "01",
        "production_order": "24640401002",
        "operation_code": "03",
        "planned_qty": 0,
        "produced_qty": 0,
        "active_appointment_count": 1,
        "active_operator_count": 1,
        "appointment_count": 1,
        "active_marker": _ACTIVE_MARKER,
    }
    assert "pending_qty" not in row
    item = MachineLoadOperationMapper.map_operation(row)
    assert item["is_in_production"] is True


# Caso real sondado em set/2026 (filial 02, OP 10964501004, operação 01):
# C2_QUANT 7,8 · C2_QUJE 1,5 · SUM(H6_QTDPROD) da operação 01 = 7,8.
_HEADER_BALANCE_ROW = {
    **_ROW,
    "branch": "02",
    "production_order": "10964501004",
    "operation_code": "01",
    "work_center": "CT-01A",
    "planned_qty": 7.8,
    "produced_qty": 1.5,
    "pending_qty": 6.3,
    "active_appointment_count": 1,
    "active_operator_count": 1,
    "appointment_count": 4,
    "active_marker": _ACTIVE_MARKER,
    "last_marker": _ACTIVE_MARKER,
}


def test_operation_balance_comes_from_appointments_not_order_header() -> None:
    """Operação apontada por inteiro sai de «Em produção» mesmo com saldo na OP."""
    item = MachineLoadOperationMapper.map_operation(
        {**_HEADER_BALANCE_ROW, "operation_produced_qty": 7.8}
    )
    assert item["pending_qty"] == 6.3
    assert item["operation_produced_qty"] == 7.8
    assert item["operation_pending_qty"] == 0.0
    assert item["production_status"] == PRODUCTION_STATUS_STARTED
    assert item["is_in_production"] is False


def test_sibling_operation_without_appointment_keeps_full_operation_balance() -> None:
    """Operação irmã da mesma OP fica com o saldo dela, não com o do cabeçalho."""
    item = MachineLoadOperationMapper.map_operation(
        {
            **_HEADER_BALANCE_ROW,
            "operation_code": "03",
            "operation_produced_qty": 0,
            "active_appointment_count": 0,
            "active_operator_count": 0,
            "appointment_count": 0,
            "active_marker": "",
            "last_marker": "",
        }
    )
    assert item["operation_pending_qty"] == 7.8
    assert item["production_status"] == PRODUCTION_STATUS_NOT_STARTED
    assert item["is_in_production"] is False


def test_partially_reported_operation_stays_in_production() -> None:
    item = MachineLoadOperationMapper.map_operation(
        {**_HEADER_BALANCE_ROW, "operation_produced_qty": 3.0}
    )
    assert item["operation_pending_qty"] == 4.8
    assert item["production_status"] == PRODUCTION_STATUS_IN_PROGRESS
    assert item["is_in_production"] is True


def test_scrap_is_not_discounted_from_the_operation_balance() -> None:
    """Peça refugada continua faltando na bancada: só H6_QTDPROD abate."""
    item = MachineLoadOperationMapper.map_operation(
        {**_HEADER_BALANCE_ROW, "operation_produced_qty": 7.5, "qty_lost": 0.3}
    )
    assert item["operation_pending_qty"] == 0.3
    assert item["is_in_production"] is True


def test_missing_operation_aggregate_keeps_header_balance_rule() -> None:
    """Sem o agregado da SH6 o saldo da operação é desconhecido, nunca zero."""
    item = MachineLoadOperationMapper.map_operation(_HEADER_BALANCE_ROW)
    assert item["operation_produced_qty"] is None
    assert item["operation_pending_qty"] is None
    assert item["is_in_production"] is True


def test_finished_order_zeroes_the_operation_balance() -> None:
    """OP encerrada zera a bancada: operação sem apontamento não fica eterna."""
    item = MachineLoadOperationMapper.map_operation(
        {
            **_HEADER_BALANCE_ROW,
            "operation_produced_qty": 0,
            "order_is_finished": 1,
            "order_finish_date": "20260915",
        }
    )
    assert item["operation_pending_qty"] == 0.0
    assert item["production_status"] == PRODUCTION_STATUS_STARTED


def test_exhausted_order_balance_zeroes_the_operation_balance() -> None:
    item = MachineLoadOperationMapper.map_operation(
        {
            **_HEADER_BALANCE_ROW,
            "produced_qty": 7.8,
            "pending_qty": 0,
            "operation_produced_qty": 0,
        }
    )
    assert item["operation_pending_qty"] == 0.0
    assert item["is_in_production"] is False


def test_two_operators_on_the_same_operation_are_counted() -> None:
    item = MachineLoadOperationMapper.map_operation(
        {
            **_ROW,
            "active_appointment_count": 2,
            "active_operator_count": 2,
            "appointment_count": 5,
            "active_marker": _ACTIVE_MARKER,
        }
    )
    assert item["active_operator_count"] == 2
    assert item["is_in_production"] is True


def test_map_work_center_counts() -> None:
    item = MachineLoadOperationMapper.map_work_center(
        {
            "work_center": "CT-02",
            "work_center_name": "APLICAÇÃO DE TERMINAIS",
            "operation_count": 42,
            "order_count": 21,
            "in_production_count": 3,
            "first_scheduled_date": "20260820",
            "last_scheduled_date": "20260826",
        }
    )
    assert item["operation_count"] == 42
    assert item["order_count"] == 21
    assert item["in_production_count"] == 3
    assert item["first_scheduled_date"] == "2026-08-20"


def test_window_defaults_to_next_seven_days() -> None:
    window = MachineLoadWindow.resolve(branch="01", today=date(2026, 8, 19))
    assert window.scheduled_start == date(2026, 8, 19)
    assert window.scheduled_end == date(2026, 8, 26)
    assert window.filter_kwargs()["scheduled_start"] == "20260819"
    assert window.filter_kwargs()["scheduled_end"] == "20260826"


def test_appointment_lookback_follows_today_not_the_chosen_period() -> None:
    """"Produzindo agora" é sempre relativo ao turno corrente."""
    window = MachineLoadWindow.resolve(
        branch="01",
        scheduled_start="2026-09-01",
        scheduled_end="2026-09-10",
        today=date(2026, 8, 19),
    )
    kwargs = window.filter_kwargs()
    assert kwargs["appointment_active_since"] == "20260817"
    assert kwargs["appointment_history_since"] == "20260720"


def test_window_rejects_invalid_branch_and_inverted_range() -> None:
    with pytest.raises(ValueError):
        MachineLoadWindow.resolve(branch="09")
    with pytest.raises(ValueError):
        MachineLoadWindow.resolve(
            branch="01",
            scheduled_start="2026-08-26",
            scheduled_end="2026-08-19",
        )


def test_window_rejects_range_over_the_limit() -> None:
    with pytest.raises(ValueError):
        MachineLoadWindow.resolve(
            branch="01",
            scheduled_start="2026-01-01",
            scheduled_end="2026-12-31",
        )


def test_operations_request_defaults_to_open_orders_and_schedule_sort() -> None:
    request = MachineLoadOperationsRequest.from_params(
        window=MachineLoadWindow.resolve(branch="01", today=date(2026, 8, 19)),
    )
    assert request.open_only is True
    assert request.sort == "schedule_asc"
    assert request.offset == 0


def test_operations_request_include_closed_clears_open_only_filter() -> None:
    request = MachineLoadOperationsRequest.from_params(
        window=MachineLoadWindow.resolve(branch="01", today=date(2026, 8, 19)),
        include_closed=True,
    )
    assert request.open_only is None


def test_operations_request_rejects_unknown_sort() -> None:
    with pytest.raises(ValueError):
        MachineLoadOperationsRequest.from_params(
            window=MachineLoadWindow.resolve(branch="01", today=date(2026, 8, 19)),
            sort="bogus",
        )
