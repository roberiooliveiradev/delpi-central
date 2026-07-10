from __future__ import annotations

import pytest

from app.application.services.audit_5s.catalog_publish_service import (
    CatalogPublishValidationError,
    catalogs_are_equal,
    normalize_criteria_snapshot,
    validate_publish_payload,
)


def _sample_criteria() -> list[dict]:
    prefixes = {1: "U", 2: "O", 3: "L", 4: "P", 5: "D"}
    return [
        {
            "senso_order": order,
            "sort_order": 1,
            "code": f"{prefixes[order]}01",
            "description": f"Critério do senso {order}",
        }
        for order in range(1, 6)
    ]


def test_validate_publish_payload_accepts_complete_catalog() -> None:
    payload = _sample_criteria()
    normalized = validate_publish_payload(criteria=payload)
    assert len(normalized) == 5


def test_validate_publish_payload_rejects_missing_senso() -> None:
    payload = _sample_criteria()[:4]
    with pytest.raises(CatalogPublishValidationError, match="Faltando"):
        validate_publish_payload(criteria=payload)


def test_validate_publish_payload_rejects_duplicate_code() -> None:
    payload = _sample_criteria()
    payload[1]["code"] = payload[0]["code"]
    with pytest.raises(CatalogPublishValidationError, match="duplicado"):
        validate_publish_payload(criteria=payload)


def test_catalogs_are_equal_detects_description_change() -> None:
    current = _sample_criteria()
    updated = _sample_criteria()
    updated[0]["description"] = "Descrição alterada"
    assert not catalogs_are_equal(
        current_criteria=current,
        next_criteria=updated,
        current_senso_names=None,
        next_senso_names=None,
    )


def test_normalize_criteria_snapshot_sorts_and_trims() -> None:
    snapshot = normalize_criteria_snapshot(
        [
            {"senso_order": 2, "sort_order": 1, "code": " o01 ", "description": "  Texto  "},
            {"senso_order": 1, "sort_order": 1, "code": "u01", "description": "Outro"},
        ]
    )
    assert snapshot[0] == (1, 1, "U01", "Outro")
    assert snapshot[1][2] == "O01"
