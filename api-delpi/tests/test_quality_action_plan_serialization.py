"""Serialização PAC — datas JSON-safe para API e snapshot de revisão."""

from __future__ import annotations

import json
from datetime import date, datetime
from uuid import UUID

from app.domain.services.quality_action_plans.pac_plan_revision_snapshot_service import (
    build_snapshot_from_detail,
)
from app.domain.services.quality_action_plans.quality_action_plan_serialization import (
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


def test_revision_snapshot_with_due_date_is_json_serializable() -> None:
    """Regressão: criar ação com prazo → record_plan_revision → json.dumps.

    Antes, ``due_date`` (DATE) permanecia como ``datetime.date`` e o dump
    estourava TypeError → 500 «Internal server error» no middleware JWT.
    """
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

    encoded = json.dumps(snapshot)
    assert "2026-07-17" in encoded
    assert '"due_date": "2026-07-17"' in encoded


def test_revision_snapshot_fails_if_raw_date_leaks() -> None:
    """Contrato negativo: date cru no snapshot não pode ir para json.dumps."""
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
    assert raised, "date cru deveria quebrar json.dumps (prova do bug original)"
