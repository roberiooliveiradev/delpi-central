"""Serialização PAC — datas JSON-safe para API e snapshot de revisão."""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.domain.services.quality_action_plans.pac_plan_revision_snapshot_service import (
    build_snapshot_from_detail,
)
from app.domain.services.quality_action_plans.quality_action_plan_serialization import (
    dumps_json_safe,
    json_safe_value,
    serialize_row,
)


def test_serialize_row_converts_date_and_datetime() -> None:
    row = serialize_row(
        {
            "id": UUID("11111111-1111-1111-1111-111111111111"),
            "plan_id": UUID("22222222-2222-2222-2222-222222222222"),
            "due_date": date(2026, 7, 17),
            "created_at": datetime(2026, 7, 1, 12, 30, 0),
            "description": "Segregar itens",
        },
        id_keys=("id", "plan_id"),
    )

    assert row is not None
    assert row["due_date"] == "2026-07-17"
    assert row["created_at"].startswith("2026-07-01T12:30:00")
    assert row["id"] == "11111111-1111-1111-1111-111111111111"
    assert row["plan_id"] == "22222222-2222-2222-2222-222222222222"


def test_serialize_row_leaves_null_due_date() -> None:
    row = serialize_row({"id": "a1", "due_date": None})
    assert row is not None
    assert row["due_date"] is None


def test_json_safe_value_nested_decimal_and_uuid() -> None:
    payload = {
        "template_payload": {"defective_quantity": Decimal("12.5"), "batch_quantity": Decimal("3")},
        "responsibles": [
            {
                "id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
                "display_name": "Aline e Geiziara",
                "user_id": None,
            }
        ],
        "due_date": date(2026, 7, 17),
    }
    safe = json_safe_value(payload)
    assert safe["template_payload"]["defective_quantity"] == 12.5
    assert safe["template_payload"]["batch_quantity"] == 3
    assert safe["responsibles"][0]["id"] == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    assert safe["due_date"] == "2026-07-17"
    json.dumps(safe)  # não deve lançar


def test_dumps_json_safe_survives_raw_postgres_types_in_snapshot() -> None:
    """Regressão produção: POST /actions com prazo + responsável livre + payload 8D."""
    snapshot = build_snapshot_from_detail(
        {
            "plan": {
                "id": UUID("5857874c-5030-4a31-b3df-fc5b88f5d966"),
                "title": "PAC",
                "template_payload": {"defective_quantity": Decimal("1")},
            },
            "actions": [
                {
                    "id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
                    "description": "Segregar e revisar",
                    "due_date": date(2026, 7, 17),
                    "status": "in_progress",
                    "responsibles": [
                        {
                            "id": UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
                            "display_name": "Aline e Geiziara",
                            "user_id": None,
                            "sort_order": 0,
                        }
                    ],
                }
            ],
        }
    )
    encoded = dumps_json_safe(snapshot)
    parsed = json.loads(encoded)
    assert parsed["actions"][0]["due_date"] == "2026-07-17"
    assert parsed["actions"][0]["responsibles"][0]["id"] == "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    assert parsed["plan"]["template_payload"]["defective_quantity"] == 1


def test_revision_snapshot_with_due_date_is_json_serializable() -> None:
    action = serialize_row(
        {
            "id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            "plan_id": UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
            "action_type": "containment",
            "description": "Segregar e revisar",
            "due_date": date(2026, 7, 17),
            "status": "in_progress",
            "cause_track": "occurrence",
            "created_at": datetime(2026, 7, 1, 10, 0, 0),
            "updated_at": datetime(2026, 7, 1, 10, 0, 0),
        },
        id_keys=("id", "plan_id"),
    )
    snapshot = build_snapshot_from_detail(
        {
            "plan": {"id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "title": "PAC"},
            "actions": [action],
        }
    )

    encoded = dumps_json_safe(snapshot)
    assert "2026-07-17" in encoded


def test_raw_json_dumps_still_fails_without_helper() -> None:
    """Prova do bug: json.dumps cru com date no snapshot quebra."""
    snapshot = build_snapshot_from_detail(
        {
            "plan": {"id": "p1", "title": "PAC"},
            "actions": [
                {
                    "id": "a1",
                    "description": "Ação",
                    "due_date": date(2026, 7, 17),
                }
            ],
        }
    )
    try:
        json.dumps(snapshot)
        raised = False
    except TypeError:
        raised = True
    assert raised
    # helper cobre o caso
    dumps_json_safe(snapshot)
