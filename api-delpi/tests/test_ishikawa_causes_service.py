from __future__ import annotations

import pytest

from app.domain.services.quality_action_plans.ishikawa_causes_service import (
    ishikawa_causes_json,
    normalize_category_causes,
    normalize_ishikawa_payload,
    serialize_ishikawa_row,
)


def test_normalize_category_causes_accepts_list():
    assert normalize_category_causes([" A ", "", "B"]) == ["A", "B"]


def test_normalize_category_causes_splits_legacy_multiline_string():
    assert normalize_category_causes("Linha 1\n- Linha 2") == ["Linha 1", "Linha 2"]


def test_ishikawa_causes_json_serializes_arrays():
    payload = normalize_ishikawa_payload(
        {"machine": ["Falha no eixo", "PM atrasada"], "material": None}
    )
    encoded = ishikawa_causes_json(payload)
    assert encoded["machine"] == '["Falha no eixo", "PM atrasada"]'
    assert encoded["material"] == "[]"


def test_serialize_ishikawa_row_returns_string_lists():
    row = serialize_ishikawa_row(
        {
            "id": "uuid",
            "plan_id": "plan",
            "machine": ["Causa 1"],
            "method_process": [],
            "material": None,
            "manpower": [],
            "measurement": [],
            "environment": [],
            "notes": "Obs",
        }
    )
    assert row is not None
    assert row["machine"] == ["Causa 1"]
    assert row["method_process"] == []
