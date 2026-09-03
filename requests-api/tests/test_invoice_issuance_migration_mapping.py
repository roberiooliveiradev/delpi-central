"""Unit tests for invoice_issuance → my_requests migration mapping (E8.S1)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from requests_app.application.services.invoice_issuance_migration_mapping import (
    build_history_row,
    build_payload,
    map_legacy_event_action,
    map_legacy_status,
    should_create_assignment,
)


@pytest.mark.parametrize(
    ("legacy", "canonical"),
    [
        ("pending", "submitted"),
        ("in_progress", "in_progress"),
        ("returned", "needs_information"),
        ("issued", "completed"),
        ("cancelled", "cancelled"),
    ],
)
def test_map_legacy_status(legacy: str, canonical: str) -> None:
    assert map_legacy_status(legacy) == canonical


def test_map_legacy_status_unknown() -> None:
    with pytest.raises(ValueError, match="desconhecido"):
        map_legacy_status("open")


@pytest.mark.parametrize(
    ("event", "action"),
    [
        ("created", "created"),
        ("started", "start"),
        ("returned", "return"),
        ("issued", "complete"),
        ("resubmitted", "resubmit"),
        ("cancelled", "cancel"),
        ("updated", "edit"),
    ],
)
def test_map_legacy_event_action(event: str, action: str) -> None:
    assert map_legacy_event_action(event) == action


def test_build_payload_includes_items_and_migration_meta() -> None:
    when = datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc)
    row = {
        "party_type": "customer",
        "party_code": "000001",
        "party_store": "01",
        "party_name": "Cliente X",
        "tax_id": "123",
        "invoice_type": "sale",
        "freight_mode": "cif",
        "carrier_code": "C01",
        "carrier_name": "Transp",
        "carrier_legal_name": "Transp LTDA",
        "weight_kg": Decimal("12.5"),
        "volume_count": 2,
        "observation": "obs",
        "checklist": {"ok": True},
        "purchase_order_number": None,
    }
    items = [
        {
            "line_number": 2,
            "product_code": "P2",
            "product_description": "Item 2",
            "quantity": Decimal("1"),
            "unit_price": Decimal("10"),
            "stock_write_off": True,
            "sales_order": "PV1",
            "sales_order_item": "01",
        },
        {
            "line_number": 1,
            "product_code": "P1",
            "product_description": "Item 1",
            "quantity": Decimal("3"),
            "unit_price": Decimal("5.5"),
            "stock_write_off": False,
            "customer_order_number": "OC-9",
        },
    ]
    payload = build_payload(row, items, legacy_id="uuid-1", migrated_at=when)

    assert payload["party_code"] == "000001"
    assert payload["weight_kg"] == 12.5
    assert payload["carrier_legal_name"] == "Transp LTDA"
    assert [item["product_code"] for item in payload["items"]] == ["P1", "P2"]
    assert payload["items"][0]["customer_order_number"] == "OC-9"
    assert payload["items"][1]["sales_order"] == "PV1"
    assert payload["_migration"]["source"] == "invoice_issuance"
    assert payload["_migration"]["legacy_id"] == "uuid-1"
    assert "2026-09-03" in payload["_migration"]["migrated_at"]
    assert "status" not in payload
    assert "assignee_user_id" not in payload


def test_build_history_row_maps_statuses_and_action() -> None:
    mapped = build_history_row(
        {
            "event_type": "issued",
            "from_status": "in_progress",
            "to_status": "issued",
            "actor_user_id": "u1",
            "actor_name": "Ana",
            "justification": None,
            "changes": {"x": 1},
            "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        }
    )
    assert mapped["action"] == "complete"
    assert mapped["from_status"] == "in_progress"
    assert mapped["to_status"] == "completed"
    assert mapped["actor_user_id"] == "u1"


def test_should_create_assignment_only_in_progress_with_assignee() -> None:
    assert should_create_assignment(
        {"status": "in_progress", "assignee_user_id": "u1"}
    )
    assert not should_create_assignment(
        {"status": "pending", "assignee_user_id": "u1"}
    )
    assert not should_create_assignment(
        {"status": "in_progress", "assignee_user_id": None}
    )


def test_cli_help_smoke() -> None:
    import subprocess
    import sys
    from pathlib import Path

    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "migrate_invoice_issuance_to_my_requests.py"
    )
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--apply" in result.stdout
    assert "dry-run" in result.stdout.lower() or "relatório" in result.stdout.lower()
