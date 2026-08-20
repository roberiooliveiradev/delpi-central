from __future__ import annotations

from typing import Any

from production_control_app.domain.services.machine_load_delivery_sequencing import (
    optimize_by_delivery_date,
)


def _op(
    order: str,
    *,
    due: str | None = None,
    center: str = "CT-01A",
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
        "production_status": status,
        "is_in_production": running,
    }


def _orders(operations: list[dict[str, Any]], center: str) -> list[str]:
    return [item["production_order"] for item in operations if item["work_center"] == center]


def test_queue_is_sorted_by_delivery_date_in_every_work_center() -> None:
    operations = [
        _op("A3", due="2026-09-30", center="CT-01A"),
        _op("A1", due="2026-08-21", center="CT-01A"),
        _op("A2", due="2026-09-02", center="CT-01A"),
        _op("B2", due="2026-10-15", center="CT-02"),
        _op("B1", due="2026-08-25", center="CT-02"),
    ]

    result = optimize_by_delivery_date(operations)

    assert sorted(result.work_centers) == ["CT-01A", "CT-02"]
    assert _orders(result.operations, "CT-01A") == ["A1", "A2", "A3"]
    assert _orders(result.operations, "CT-02") == ["B1", "B2"]
    assert result.kept_ahead_count == 0


def test_same_delivery_date_keeps_the_current_manual_order() -> None:
    operations = [
        _op("A2", due="2026-08-21"),
        _op("A1", due="2026-08-21"),
        _op("A0", due="2026-08-20"),
    ]

    result = optimize_by_delivery_date(operations)

    # A0 sobe por ser mais antiga; A2 continua na frente de A1 (mesma entrega).
    assert _orders(result.operations, "CT-01A") == ["A0", "A2", "A1"]


def test_started_operation_is_never_overtaken() -> None:
    operations = [
        _op("A9", due="2026-12-01", running=True),
        _op("A3", due="2026-09-30"),
        _op("A1", due="2026-08-21"),
    ]

    result = optimize_by_delivery_date(operations)

    assert _orders(result.operations, "CT-01A") == ["A9", "A1", "A3"]
    assert result.kept_ahead_count == 1


def test_appointed_operation_in_the_middle_holds_its_slot() -> None:
    operations = [
        _op("A3", due="2026-09-30"),
        _op("A9", due="2026-12-01", status="started"),
        _op("A1", due="2026-08-21"),
    ]

    result = optimize_by_delivery_date(operations)

    # A posição 2 é da operação já apontada; só as livres (1ª e 3ª) trocam entre si.
    assert _orders(result.operations, "CT-01A") == ["A1", "A9", "A3"]


def test_live_status_keys_pin_operations_without_snapshot_flags() -> None:
    operations = [
        _op("A9", due="2026-12-01", operation="07"),
        _op("A3", due="2026-09-30", operation="03"),
        _op("A1", due="2026-08-21", operation="02"),
    ]

    result = optimize_by_delivery_date(operations, started_keys={("A9", "07")})

    assert _orders(result.operations, "CT-01A") == ["A9", "A1", "A3"]
    assert result.kept_ahead_count == 1


def test_operation_without_delivery_goes_to_the_end() -> None:
    operations = [
        _op("A0"),
        _op("A2", due="2026-09-02"),
        _op("A1", due="2026-08-21"),
    ]

    result = optimize_by_delivery_date(operations)

    assert _orders(result.operations, "CT-01A") == ["A1", "A2", "A0"]
    assert result.missing_due_date_count == 1


def test_snapshot_without_due_date_falls_back_to_pa_due_date() -> None:
    operations = [
        _op("A2", pa_due="2026-09-02"),
        _op("A1", pa_due="2026-08-21"),
    ]

    result = optimize_by_delivery_date(operations)

    assert _orders(result.operations, "CT-01A") == ["A1", "A2"]
    assert result.missing_due_date_count == 0


def test_queue_already_sorted_reports_no_change() -> None:
    operations = [
        _op("A1", due="2026-08-21"),
        _op("A2", due="2026-09-02"),
    ]

    result = optimize_by_delivery_date(operations)

    assert result.work_centers == []
    assert result.moved_operation_count == 0
    assert result.operations == operations


def test_center_with_only_started_operations_is_untouched() -> None:
    operations = [
        _op("A9", due="2026-12-01", running=True),
        _op("A1", due="2026-08-21", status="started"),
    ]

    result = optimize_by_delivery_date(operations)

    assert result.work_centers == []
    assert _orders(result.operations, "CT-01A") == ["A9", "A1"]


def test_moved_count_reports_only_operations_that_changed_position() -> None:
    operations = [
        _op("A1", due="2026-08-21"),
        _op("A3", due="2026-09-30"),
        _op("A2", due="2026-09-02"),
    ]

    result = optimize_by_delivery_date(operations)

    assert _orders(result.operations, "CT-01A") == ["A1", "A2", "A3"]
    assert result.moved_operation_count == 2
