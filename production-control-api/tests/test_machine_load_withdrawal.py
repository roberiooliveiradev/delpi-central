from __future__ import annotations

from typing import Any

from production_control_app.domain.services.machine_load_withdrawal import (
    build_withdrawal_entry,
    is_withdrawn,
    restore_conjunto,
    visible_operations,
    withdraw_conjunto,
    withdrawn_entries,
    withdrawn_operations,
    withdrawn_order_numbers,
)


def _op(order: str, *, center: str = "CT-01A", operation: str = "01", pa: str | None = "90262910"):
    return {
        "work_center": center,
        "production_order": order,
        "operation_code": operation,
        "pa_product_code": pa,
        "pa_due_date": "2026-08-24",
    }


_OPERATIONS: list[dict[str, Any]] = [
    _op("10840401003", operation="01"),
    _op("10840402001", center="CT-08D", operation="02"),
    _op("99900001001", center="CT-08D", operation="01", pa="90111111"),
]


def test_withdrawn_keys_are_read_from_payload() -> None:
    payload = {"withdrawn_conjuntos": [{"order_number": "108404"}, {"no_key": 1}, "lixo"]}
    assert withdrawn_order_numbers(payload) == {"108404"}
    assert len(withdrawn_entries(payload)) == 1
    assert withdrawn_order_numbers({}) == set()


def test_is_withdrawn_matches_every_order_of_the_conjunto() -> None:
    keys = {"108404"}
    assert is_withdrawn(_op("10840401003"), keys) is True
    assert is_withdrawn(_op("10840402001"), keys) is True
    assert is_withdrawn(_op("99900001001"), keys) is False
    assert is_withdrawn(_op("10840401003"), set()) is False


def test_visible_and_withdrawn_split_keeps_order() -> None:
    keys = {"108404"}
    visible = visible_operations(_OPERATIONS, keys)
    hidden = withdrawn_operations(_OPERATIONS, keys)

    assert [item["production_order"] for item in visible] == ["99900001001"]
    assert [item["production_order"] for item in hidden] == ["10840401003", "10840402001"]
    assert visible_operations(_OPERATIONS, set()) == _OPERATIONS


def test_entry_summarizes_product_centers_and_count() -> None:
    entry = build_withdrawal_entry(
        order_number="108404",
        operations=_OPERATIONS,
        withdrawn_at="2026-08-20T15:00:00+00:00",
        withdrawn_by="Michael",
    )

    assert entry["order_number"] == "108404"
    assert entry["operation_count"] == 2
    assert entry["work_centers"] == ["CT-01A", "CT-08D"]
    assert entry["pa_product_code"] == "90262910"
    assert entry["pa_due_date"] == "2026-08-24"
    assert entry["withdrawn_by"] == "Michael"


def test_withdraw_accepts_full_order_and_is_idempotent() -> None:
    entries, changed = withdraw_conjunto(
        [],
        order_number="10840401003",
        operations=_OPERATIONS,
        withdrawn_at="2026-08-20T15:00:00+00:00",
        withdrawn_by="Michael",
    )
    assert changed is True
    assert [item["order_number"] for item in entries] == ["108404"]

    again, changed_again = withdraw_conjunto(
        entries,
        order_number="108404",
        operations=_OPERATIONS,
        withdrawn_at="2026-08-20T16:00:00+00:00",
        withdrawn_by="Outro",
    )
    assert changed_again is False
    assert again == entries


def test_withdraw_rejects_short_order_number() -> None:
    entries, changed = withdraw_conjunto(
        [],
        order_number="1084",
        operations=_OPERATIONS,
        withdrawn_at="2026-08-20T15:00:00+00:00",
        withdrawn_by=None,
    )
    assert changed is False
    assert entries == []


def test_restore_removes_only_the_requested_conjunto() -> None:
    entries = [{"order_number": "108404"}, {"order_number": "246404"}]

    remaining, changed = restore_conjunto(entries, order_number="10840401003")
    assert changed is True
    assert [item["order_number"] for item in remaining] == ["246404"]

    untouched, changed_again = restore_conjunto(remaining, order_number="108404")
    assert changed_again is False
    assert untouched == remaining
