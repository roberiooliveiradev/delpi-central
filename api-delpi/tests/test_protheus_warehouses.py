"""Constantes compartilhadas de armazém / custo Protheus."""

from app.domain.totvs.protheus_warehouses import (
    AVAILABLE_BALANCE_WAREHOUSES,
    COST_UNIT_WAREHOUSE,
    WAREHOUSE_ALMOXARIFADO,
    WAREHOUSE_FABRICA,
    WORK_IN_PROCESS_WAREHOUSES,
)


def test_cost_unit_warehouse_is_almoxarifado() -> None:
    assert COST_UNIT_WAREHOUSE == WAREHOUSE_ALMOXARIFADO == "01"
    assert WAREHOUSE_FABRICA == "99"
    assert WAREHOUSE_FABRICA not in (COST_UNIT_WAREHOUSE,)


def test_available_balance_includes_almox_and_factory() -> None:
    assert AVAILABLE_BALANCE_WAREHOUSES == ("01", "98", "99")
    assert set(WORK_IN_PROCESS_WAREHOUSES) == {"50", "98", "99"}
