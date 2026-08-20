from __future__ import annotations

from typing import Any

from production_control_app.domain.services.machine_load_priority import prioritize_conjunto
from production_control_app.domain.services.machine_load_queue_slots import (
    is_started_operation,
)


def _op(
    order: str,
    *,
    center: str = "CT-01A",
    operation: str = "01",
    status: str = "not_started",
    running: bool = False,
) -> dict[str, Any]:
    return {
        "work_center": center,
        "production_order": order,
        "operation_code": operation,
        "production_status": status,
        "is_in_production": running,
    }


def _orders(operations: list[dict[str, Any]], center: str) -> list[str]:
    return [
        f"{item['production_order']}:{item['operation_code']}"
        for item in operations
        if item["work_center"] == center
    ]


def test_started_detection_covers_running_and_appointed() -> None:
    assert is_started_operation(_op("1", running=True)) is True
    assert is_started_operation(_op("1", status="in_progress")) is True
    assert is_started_operation(_op("1", status="started")) is True
    assert is_started_operation(_op("1")) is False


def test_conjunto_goes_to_top_of_each_work_center() -> None:
    operations = [
        _op("99900001001", center="CT-01A", operation="01"),
        _op("88800001001", center="CT-01A", operation="01"),
        _op("10840401003", center="CT-01A", operation="01"),
        _op("77700001001", center="CT-02", operation="01"),
        _op("10840402001", center="CT-02", operation="05"),
    ]

    result = prioritize_conjunto(operations, conjunto_key="108404")

    assert sorted(result.work_centers) == ["CT-01A", "CT-02"]
    assert result.prioritized_operation_count == 2
    assert result.kept_ahead_count == 0
    assert _orders(result.operations, "CT-01A")[0] == "10840401003:01"
    assert _orders(result.operations, "CT-02")[0] == "10840402001:05"


def test_started_operation_stays_ahead_and_conjunto_is_next() -> None:
    operations = [
        _op("99900001001", operation="01", running=True),
        _op("88800001001", operation="02"),
        _op("10840401003", operation="03"),
    ]

    result = prioritize_conjunto(operations, conjunto_key="108404")

    assert _orders(result.operations, "CT-01A") == [
        "99900001001:01",
        "10840401003:03",
        "88800001001:02",
    ]
    assert result.kept_ahead_count == 1


def test_all_orders_of_conjunto_move_together_keeping_relative_order() -> None:
    operations = [
        _op("55500001001", operation="01"),
        _op("10840402001", operation="02"),
        _op("66600001001", operation="03"),
        _op("10840401003", operation="04"),
    ]

    result = prioritize_conjunto(operations, conjunto_key="108404")

    assert _orders(result.operations, "CT-01A") == [
        "10840402001:02",
        "10840401003:04",
        "55500001001:01",
        "66600001001:03",
    ]
    assert result.prioritized_operation_count == 2


def test_already_started_conjunto_operation_is_not_moved() -> None:
    operations = [
        _op("99900001001", operation="01"),
        _op("10840401003", operation="02", status="started"),
        _op("10840402001", operation="03"),
    ]

    result = prioritize_conjunto(operations, conjunto_key="108404")

    assert _orders(result.operations, "CT-01A") == [
        "10840402001:03",
        "10840401003:02",
        "99900001001:01",
    ]
    assert result.prioritized_operation_count == 1


def test_live_status_keys_pin_operations_without_snapshot_flags() -> None:
    operations = [
        _op("99900001001", operation="01"),
        _op("10840401003", operation="02"),
    ]

    result = prioritize_conjunto(
        operations,
        conjunto_key="108404",
        started_keys={("99900001001", "01")},
    )

    assert _orders(result.operations, "CT-01A") == [
        "99900001001:01",
        "10840401003:02",
    ]
    assert result.kept_ahead_count == 1


def test_center_without_conjunto_is_untouched() -> None:
    operations = [
        _op("99900001001", center="CT-09", operation="01"),
        _op("88800001001", center="CT-09", operation="02"),
    ]

    result = prioritize_conjunto(operations, conjunto_key="108404")

    assert result.work_centers == []
    assert result.prioritized_operation_count == 0
    assert result.operations == operations
