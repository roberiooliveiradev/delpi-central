from __future__ import annotations

from typing import Any

from production_control_app.domain.services.machine_load_transfer import (
    apply_transfers,
    find_operation,
    move_operation,
    original_work_center,
    register_transfer,
    transfer_entries,
)


def _op(order: str, operation: str, center: str) -> dict[str, Any]:
    return {
        "work_center": center,
        "work_center_name": f"NOME {center}",
        "production_order": order,
        "operation_code": operation,
    }


def _queue(operations: list[dict[str, Any]]) -> list[str]:
    return [
        f"{item['work_center']}:{item['production_order']}:{item['operation_code']}"
        for item in operations
    ]


_OPERATIONS = [
    _op("10840401003", "01", "CT-01A"),
    _op("99900001001", "01", "CT-01A"),
    _op("77700001001", "01", "CT-02"),
    _op("88800001001", "02", "CT-02"),
]


def test_move_operation_puts_it_at_the_end_of_the_target_queue() -> None:
    moved = move_operation(
        _OPERATIONS,
        production_order="10840401003",
        operation_code="01",
        target_work_center="CT-02",
        target_work_center_name="APLICAÇÃO DE TERMINAIS",
    )

    assert moved is not None
    assert moved.source_work_center == "CT-01A"
    assert moved.target_work_center == "CT-02"
    assert _queue(moved.operations) == [
        "CT-01A:99900001001:01",
        "CT-02:77700001001:01",
        "CT-02:88800001001:02",
        "CT-02:10840401003:01",
    ]
    assert moved.operation["work_center_name"] == "APLICAÇÃO DE TERMINAIS"
    assert moved.operation["transferred_from"] == "CT-01A"
    # A lista original não é mutada.
    assert _OPERATIONS[0]["work_center"] == "CT-01A"


def test_move_conjunto_at_work_center_only_moves_ops_in_that_center() -> None:
    """Mesmo C2_NUM em outro CT não sai da fila dele."""
    from production_control_app.domain.services.machine_load_transfer import (
        move_conjunto_at_work_center,
    )

    queue = [
        _op("10840401003", "01", "CT-01A"),
        _op("10840401003", "02", "CT-01A"),
        _op("99900001001", "01", "CT-01A"),
        _op("10840402001", "05", "CT-02"),
        _op("77700001001", "01", "CT-02"),
    ]
    moved = move_conjunto_at_work_center(
        queue,
        conjunto_key="108404",
        source_work_center="CT-01A",
        target_work_center="CT-02",
        target_work_center_name="DESTINO",
    )

    assert moved is not None
    assert len(moved.moved) == 2
    assert _queue(moved.operations) == [
        "CT-01A:99900001001:01",
        "CT-02:10840402001:05",
        "CT-02:77700001001:01",
        "CT-02:10840401003:01",
        "CT-02:10840401003:02",
    ]
    assert all(item["transferred_from"] == "CT-01A" for item in moved.moved)
    assert moved.operations[1]["production_order"] == "10840402001"
    assert "transferred_from" not in moved.operations[1]


def test_move_operation_to_empty_center_appends_at_the_end() -> None:
    moved = move_operation(
        _OPERATIONS,
        production_order="77700001001",
        operation_code="01",
        target_work_center="CT-09",
    )

    assert moved is not None
    assert _queue(moved.operations)[-1] == "CT-09:77700001001:01"


def test_move_operation_back_to_origin_clears_the_transfer_mark() -> None:
    first = move_operation(
        _OPERATIONS,
        production_order="10840401003",
        operation_code="01",
        target_work_center="CT-02",
    )
    assert first is not None

    back = move_operation(
        first.operations,
        production_order="10840401003",
        operation_code="01",
        target_work_center="CT-01A",
        origin_work_center="CT-01A",
    )

    assert back is not None
    assert "transferred_from" not in back.operation
    assert _queue(back.operations)[1] == "CT-01A:10840401003:01"


def test_move_operation_returns_none_for_unknown_operation_or_center() -> None:
    assert (
        move_operation(
            _OPERATIONS,
            production_order="12345678901",
            operation_code="01",
            target_work_center="CT-02",
        )
        is None
    )
    assert (
        move_operation(
            _OPERATIONS,
            production_order="10840401003",
            operation_code="01",
            target_work_center="  ",
        )
        is None
    )


def test_find_operation_matches_order_and_operation_code() -> None:
    assert find_operation(_OPERATIONS, production_order="88800001001", operation_code="02")
    assert find_operation(_OPERATIONS, production_order="88800001001", operation_code="01") is None


def test_entries_keep_one_row_per_operation_and_the_original_center() -> None:
    entries = register_transfer(
        [],
        production_order="10840401003",
        operation_code="01",
        origin_work_center="CT-01A",
        target_work_center="CT-02",
        transferred_at="2026-08-20T15:00:00+00:00",
        transferred_by="Michael",
    )
    assert [item["target_work_center"] for item in entries] == ["CT-02"]

    origin = original_work_center(
        entries, production_order="10840401003", operation_code="01", fallback="CT-02"
    )
    assert origin == "CT-01A"

    entries = register_transfer(
        entries,
        production_order="10840401003",
        operation_code="01",
        origin_work_center=origin,
        target_work_center="CT-09",
        transferred_at="2026-08-20T16:00:00+00:00",
        transferred_by="Michael",
    )
    assert len(entries) == 1
    assert entries[0]["source_work_center"] == "CT-01A"
    assert entries[0]["target_work_center"] == "CT-09"


def test_returning_to_the_origin_drops_the_entry() -> None:
    entries = register_transfer(
        [],
        production_order="10840401003",
        operation_code="01",
        origin_work_center="CT-01A",
        target_work_center="CT-02",
        transferred_at="2026-08-20T15:00:00+00:00",
        transferred_by="Michael",
    )

    entries = register_transfer(
        entries,
        production_order="10840401003",
        operation_code="01",
        origin_work_center="CT-01A",
        target_work_center="CT-01A",
        transferred_at="2026-08-20T17:00:00+00:00",
        transferred_by="Michael",
    )

    assert entries == []


def test_apply_transfers_replays_over_a_fresh_queue() -> None:
    entries = [
        {
            "production_order": "10840401003",
            "operation_code": "01",
            "source_work_center": "CT-01A",
            "target_work_center": "CT-02",
        }
    ]

    replayed = apply_transfers(
        _OPERATIONS,
        entries,
        work_center_names={"CT-02": "APLICAÇÃO DE TERMINAIS"},
    )

    assert _queue(replayed)[-1] == "CT-02:10840401003:01"
    assert replayed[-1]["work_center_name"] == "APLICAÇÃO DE TERMINAIS"
    # Operação que sumiu do TOTVS não quebra o replay.
    assert apply_transfers([], entries) == []


def test_transfer_entries_ignores_malformed_rows() -> None:
    payload = {
        "transferred_operations": [
            {"production_order": "10840401003", "operation_code": "01", "target_work_center": "CT-02"},
            {"production_order": "10840401003"},
            "lixo",
        ]
    }
    assert len(transfer_entries(payload)) == 1
    assert transfer_entries({}) == []
