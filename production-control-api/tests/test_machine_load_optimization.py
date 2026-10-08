"""Motor de sequenciamento composto da carga máquina (O1).

Data de entrega é sempre o critério primário e obrigatório; o agrupamento por
ferramenta é opcional e nunca atravessa fronteira de data.
"""

from __future__ import annotations

from typing import Any

from production_control_app.domain.services.machine_load_optimization import (
    MANUAL_LABOR_TOOL_CODE,
    MachineLoadOptimizationCriteria,
    MachineLoadOptimizationResult,
    normalize_tool_group,
    optimize_machine_load_queue,
)
from production_control_app.domain.services.machine_load_delivery_sequencing import (
    DeliverySequencing,
    optimize_by_delivery_date,
)

GROUP_BY_TOOL = MachineLoadOptimizationCriteria(group_by_tool=True)
DATE_ONLY = MachineLoadOptimizationCriteria(group_by_tool=False)


def _op(
    order: str,
    *,
    due: str | None = None,
    tool: str | None = "MA-00",
    center: str = "CT-01",
    operation: str = "01",
    status: str = "not_started",
    running: bool = False,
    pa_due: str | None = None,
) -> dict[str, Any]:
    return {
        "work_center": center,
        "production_order": order,
        "operation_code": operation,
        "due_date": due,
        "pa_due_date": pa_due,
        "tool": tool,
        "production_status": status,
        "is_in_production": running,
    }


def _seq(operations: list[dict[str, Any]], center: str = "CT-01") -> list[str]:
    return [item["production_order"] for item in operations if item["work_center"] == center]


def _tools(operations: list[dict[str, Any]], center: str = "CT-01") -> list[str | None]:
    return [item.get("tool") for item in operations if item["work_center"] == center]


def _optimize(operations: list[dict[str, Any]], **kwargs: Any) -> MachineLoadOptimizationResult:
    return optimize_machine_load_queue(operations, criteria=GROUP_BY_TOOL, **kwargs)


# ---------------------------------------------------------------------------
# normalize_tool_group
# ---------------------------------------------------------------------------


def test_normalize_tool_group_strips_and_uppercases() -> None:
    assert normalize_tool_group("MA-01") == "MA-01"
    assert normalize_tool_group(" ma-01 ") == "MA-01"


def test_normalize_tool_group_maps_manual_and_empty_to_no_tool() -> None:
    assert MANUAL_LABOR_TOOL_CODE == "MOD"
    for raw in ("MOD", "mod", " Mod ", "", "   ", None):
        assert normalize_tool_group(raw) is None


# ---------------------------------------------------------------------------
# A — compatibilidade data-only
# ---------------------------------------------------------------------------


def test_date_only_criteria_matches_optimize_by_delivery_date() -> None:
    operations = [
        _op("A3", due="2026-10-08", tool="MA-02"),
        _op("A1", due="2026-10-07", tool="MA-01"),
        _op("A2", due="2026-10-08", tool="MA-01"),
    ]

    via_engine = optimize_machine_load_queue(
        operations, criteria=DATE_ONLY
    )
    via_wrapper = optimize_by_delivery_date(operations)

    assert isinstance(via_wrapper, DeliverySequencing)
    assert _seq(via_engine.operations) == _seq(via_wrapper.operations) == ["A1", "A3", "A2"]
    assert via_engine.moved_operation_count == via_wrapper.moved_operation_count


# ---------------------------------------------------------------------------
# B — data continua prioritária sobre ferramenta
# ---------------------------------------------------------------------------


def test_tool_never_crosses_delivery_date_boundary() -> None:
    operations = [
        _op("A", due="2026-10-08", tool="MA-01"),
        _op("B", due="2026-10-07", tool="MA-02"),
        _op("C", due="2026-10-08", tool="MA-01"),
        _op("D", due="2026-10-07", tool="MA-03"),
    ]

    result = _optimize(operations)

    assert _seq(result.operations) == ["B", "D", "A", "C"]
    assert _tools(result.operations) == ["MA-02", "MA-03", "MA-01", "MA-01"]


# ---------------------------------------------------------------------------
# C — mesma data agrupa ferramenta
# ---------------------------------------------------------------------------


def test_same_date_groups_by_tool() -> None:
    operations = [
        _op("A", due="2026-10-08", tool="MA-01"),
        _op("B", due="2026-10-08", tool="MA-02"),
        _op("C", due="2026-10-08", tool="MA-01"),
        _op("D", due="2026-10-08", tool="MA-02"),
    ]

    result = _optimize(operations)

    assert _seq(result.operations) == ["A", "C", "B", "D"]
    assert _tools(result.operations) == ["MA-01", "MA-01", "MA-02", "MA-02"]


# ---------------------------------------------------------------------------
# D — ordem dos grupos pela primeira ocorrência, nunca alfabética
# ---------------------------------------------------------------------------


def test_tool_group_order_follows_first_occurrence_not_alphabet() -> None:
    operations = [
        _op("A", due="2026-10-08", tool="MA-20"),
        _op("B", due="2026-10-08", tool="MA-10"),
        _op("C", due="2026-10-08", tool="MA-20"),
        _op("D", due="2026-10-08", tool="MA-30"),
        _op("E", due="2026-10-08", tool="MA-10"),
    ]

    result = _optimize(operations)

    assert _seq(result.operations) == ["A", "C", "B", "E", "D"]
    assert _tools(result.operations) == [
        "MA-20",
        "MA-20",
        "MA-10",
        "MA-10",
        "MA-30",
    ]


# ---------------------------------------------------------------------------
# E/F/G — MOD, vazio e null formam o grupo sem ferramenta (depois das reais)
# ---------------------------------------------------------------------------


def test_mod_goes_after_real_tools_of_the_same_date() -> None:
    operations = [
        _op("A", due="2026-10-08", tool="MOD"),
        _op("B", due="2026-10-08", tool="MA-01"),
        _op("C", due="2026-10-08", tool="MOD"),
        _op("D", due="2026-10-08", tool="MA-01"),
    ]

    result = _optimize(operations)

    assert _seq(result.operations) == ["B", "D", "A", "C"]
    assert _tools(result.operations) == ["MA-01", "MA-01", "MOD", "MOD"]


def test_empty_and_null_tools_share_the_no_tool_group() -> None:
    operations = [
        _op("A", due="2026-10-08", tool=""),
        _op("B", due="2026-10-08", tool="MA-01"),
        _op("C", due="2026-10-08", tool=None),
        _op("D", due="2026-10-08", tool="   "),
        _op("E", due="2026-10-08", tool="mod"),
        _op("F", due="2026-10-08", tool="MA-01"),
    ]

    result = _optimize(operations)

    # Ferramenta real primeiro; grupo sem ferramenta preserva a ordem original.
    assert _seq(result.operations) == ["B", "F", "A", "C", "D", "E"]
    assert _tools(result.operations) == ["MA-01", "MA-01", "", None, "   ", "mod"]


# ---------------------------------------------------------------------------
# H — caixa/espaço não alteram o valor original do item
# ---------------------------------------------------------------------------


def test_tool_normalization_keeps_the_original_values() -> None:
    operations = [
        _op("A", due="2026-10-08", tool=" MA-01 "),
        _op("B", due="2026-10-08", tool="MA-02"),
        _op("C", due="2026-10-08", tool="ma-01"),
        _op("D", due="2026-10-08", tool="MA-01"),
    ]

    result = _optimize(operations)

    assert _seq(result.operations) == ["A", "C", "D", "B"]
    assert _tools(result.operations) == [" MA-01 ", "ma-01", "MA-01", "MA-02"]


# ---------------------------------------------------------------------------
# I/J — sem data vai ao fim e não é reagrupada por ferramenta
# ---------------------------------------------------------------------------


def test_operations_without_due_date_go_to_the_end_ungrouped() -> None:
    operations = [
        _op("A", tool="MA-02"),
        _op("B", tool="MA-01"),
        _op("C", tool="MA-02"),
        _op("D", due="2026-10-08", tool="MA-09"),
    ]

    result = _optimize(operations)

    assert _seq(result.operations) == ["D", "A", "B", "C"]
    assert result.missing_due_date_count == 3


# ---------------------------------------------------------------------------
# K/L — operações iniciadas travadas, mesmo com ferramenta ativa
# ---------------------------------------------------------------------------


def test_started_operations_hold_slots_with_tool_grouping() -> None:
    operations = [
        _op("X", due="2026-10-08", tool="MA-99", running=True),
        _op("A", due="2026-10-08", tool="MA-02"),
        _op("S", due="2026-10-08", tool="MA-02", status="started"),
        _op("B", due="2026-10-08", tool="MA-01"),
        _op("C", due="2026-10-08", tool="MA-02"),
        _op("K", due="2026-10-08", tool="MA-01", operation="07"),
    ]

    result = _optimize(operations, started_keys={("K", "07")})

    # Slots 0, 2 e 5 travados (running, status e started_keys); as livres
    # reagrupam MA-02 (A, C) antes de MA-01 (B) pela primeira ocorrencia livre.
    assert _seq(result.operations) == ["X", "A", "S", "C", "B", "K"]
    assert result.kept_ahead_count == 1
    assert result.moved_operation_count == 2


def test_pinned_tool_does_not_command_free_group_order() -> None:
    operations = [
        _op("X", due="2026-10-08", tool="MA-99", running=True),
        _op("A", due="2026-10-08", tool="MA-20"),
        _op("B", due="2026-10-08", tool="MA-10"),
        _op("C", due="2026-10-08", tool="MA-20"),
    ]

    result = _optimize(operations)

    # MA-99 da iniciada não vira grupo: livres seguem primeira ocorrência livre.
    assert _seq(result.operations) == ["X", "A", "C", "B"]


def test_started_operation_in_the_middle_holds_its_slot() -> None:
    operations = [
        _op("A", due="2026-10-08", tool="MA-02"),
        _op("S", due="2026-10-08", tool="MA-02", status="started"),
        _op("B", due="2026-10-08", tool="MA-01"),
        _op("C", due="2026-10-08", tool="MA-02"),
    ]

    result = _optimize(operations)

    assert _seq(result.operations) == ["A", "S", "C", "B"]


# ---------------------------------------------------------------------------
# M — cada CT tem ranking próprio de primeira ocorrência
# ---------------------------------------------------------------------------


def test_work_centers_have_independent_tool_group_rankings() -> None:
    operations = [
        _op("A1", due="2026-10-08", tool="MA-20", center="CT-01"),
        _op("A2", due="2026-10-08", tool="MA-10", center="CT-01"),
        _op("B1", due="2026-10-08", tool="MA-10", center="CT-02"),
        _op("B2", due="2026-10-08", tool="MA-20", center="CT-02"),
        _op("B3", due="2026-10-08", tool="MA-10", center="CT-02"),
    ]

    result = _optimize(operations)

    assert _seq(result.operations, "CT-01") == ["A1", "A2"]
    assert _seq(result.operations, "CT-02") == ["B1", "B3", "B2"]


# ---------------------------------------------------------------------------
# N — mesma data + mesma ferramenta preserva a ordem manual
# ---------------------------------------------------------------------------


def test_same_date_same_tool_keeps_manual_order() -> None:
    operations = [
        _op("A", due="2026-10-08", tool="MA-01"),
        _op("B", due="2026-10-08", tool="MA-01"),
        _op("C", due="2026-10-08", tool="MA-01"),
    ]

    result = _optimize(operations)

    assert _seq(result.operations) == ["A", "B", "C"]
    assert result.work_centers == []


# ---------------------------------------------------------------------------
# O/P — filas só com MOD ou só com vazios não mudam
# ---------------------------------------------------------------------------


def test_queue_with_only_mod_tools_is_unchanged() -> None:
    operations = [
        _op("A", due="2026-10-08", tool="MOD"),
        _op("B", due="2026-10-08", tool="mod"),
        _op("C", due="2026-10-08", tool="MOD"),
    ]

    result = _optimize(operations)

    assert _seq(result.operations) == ["A", "B", "C"]
    assert result.work_centers == []


def test_queue_with_only_empty_tools_is_unchanged() -> None:
    operations = [
        _op("A", due="2026-10-08", tool=""),
        _op("B", due="2026-10-08", tool=None),
        _op("C", due="2026-10-08", tool="   "),
    ]

    result = _optimize(operations)

    assert _seq(result.operations) == ["A", "B", "C"]
    assert result.work_centers == []


# ---------------------------------------------------------------------------
# Q/R — fila já otimizada e contagem de movidas
# ---------------------------------------------------------------------------


def test_already_optimized_queue_reports_no_change() -> None:
    operations = [
        _op("A", due="2026-10-07", tool="MA-02"),
        _op("B", due="2026-10-08", tool="MA-01"),
        _op("C", due="2026-10-08", tool="MA-01"),
    ]

    result = _optimize(operations)

    assert result.work_centers == []
    assert result.moved_operation_count == 0


def test_moved_count_reports_only_ops_that_changed_free_slot() -> None:
    operations = [
        _op("A", due="2026-10-08", tool="MA-01"),
        _op("B", due="2026-10-08", tool="MA-02"),
        _op("C", due="2026-10-08", tool="MA-01"),
    ]

    result = _optimize(operations)

    assert _seq(result.operations) == ["A", "C", "B"]
    assert result.moved_operation_count == 2


# ---------------------------------------------------------------------------
# S/T — fallback pa_due_date e fila vazia
# ---------------------------------------------------------------------------


def test_pa_due_date_fallback_still_applies_with_tool_grouping() -> None:
    operations = [
        _op("A", pa_due="2026-10-08", tool="MA-02"),
        _op("B", pa_due="2026-10-07", tool="MA-01"),
    ]

    result = _optimize(operations)

    assert _seq(result.operations) == ["B", "A"]
    assert result.missing_due_date_count == 0


def test_empty_queue_returns_empty_result() -> None:
    result = _optimize([])

    assert result.operations == []
    assert result.work_centers == []
    assert result.moved_operation_count == 0
    assert result.missing_due_date_count == 0


# ---------------------------------------------------------------------------
# Caso canônico do negócio — documentação executável da regra combinada
# ---------------------------------------------------------------------------


def test_canonical_delivery_then_tool_grouping() -> None:
    operations = [
        _op("A", due="2026-10-08", tool="MA-01"),
        _op("B", due="2026-10-07", tool="MA-02"),
        _op("C", due="2026-10-08", tool="MA-02"),
        _op("D", due="2026-10-07", tool="MA-01"),
        _op("E", due="2026-10-08", tool="MA-01"),
        _op("F", due="2026-10-07", tool="MA-02"),
        _op("G", due="2026-10-08", tool="MOD"),
        _op("H", due="2026-10-08", tool="MA-02"),
    ]

    result = _optimize(operations)

    # 07/10: primeira ferramenta livre é MA-02 → B, F, depois MA-01 → D.
    # 08/10: MA-01 (A, E), MA-02 (C, H), sem ferramenta por último (G).
    assert _seq(result.operations) == ["B", "F", "D", "A", "E", "C", "H", "G"]
