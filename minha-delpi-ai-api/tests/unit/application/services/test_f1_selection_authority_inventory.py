"""E0.S1 — freeze F1 selection-authority inventory (pre-cutover residual map)."""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_INVENTORY = (
    _ROOT / "tests/fixtures/intelligence_baseline/f1_selection_authority_inventory.json"
)

_REQUIRED_IDS = {
    "operational_route_registry_file",
    "OperationalRoute_selection_stack",
    "customPredicate_registry_match",
    "pathContains_selection_prioritization",
    "operationIdContains_selection",
    "operationIdContains_column_labels",
    "follow_up_routeSegment_preferredRouteId",
    "intentBinding_fast_path",
    "paginatedPathFragments",
    "select_operational_registry",
    "ExternalActionSelectionPreflightService",
    "operational_route_suggest_admin",
    "registrySelectionShadow_cutover",
    "openapi_first_bridge_primary",
}

_ALLOWED_STATUS = {
    "AUTHORITY",
    "AUTHORITY_PARTIAL",
    "SHADOW",
    "DEAD",
    "COLD_ADMIN",
    "F2",
    "CANONICAL",
}


def _load() -> dict:
    return json.loads(_INVENTORY.read_text(encoding="utf-8"))


def test_f1_inventory_covers_required_residuals():
    data = _load()
    ids = {str(r.get("id") or "") for r in data.get("residuals") or []}
    assert _REQUIRED_IDS.issubset(ids)


def test_f1_inventory_each_item_has_status_and_target():
    data = _load()
    for item in data["residuals"]:
        rid = item.get("id")
        status = item.get("status")
        assert status in _ALLOWED_STATUS, (rid, status)
        assert str(item.get("justification") or "").strip(), rid
        assert str(item.get("f1Target") or "").strip(), rid


def test_f1_inventory_surfaces_exist_when_listed():
    """Positive: listed surface paths exist on disk."""
    data = _load()
    for item in data["residuals"]:
        for rel in item.get("surfaces") or []:
            path = _ROOT / rel
            assert path.is_file(), (item.get("id"), rel)
        for rel in item.get("coreConsumers") or []:
            path = _ROOT / rel
            assert path.is_file(), (item.get("id"), rel)


def test_f1_inventory_cold_path_preserved_exists():
    """Sibling: OpenAPI-first cold path modules listed and present."""
    data = _load()
    cold = data.get("coldPathPreserved") or []
    assert len(cold) >= 5
    for rel in cold:
        assert (_ROOT / rel).is_file(), rel


def test_f1_inventory_negative_column_labels_is_f2_not_authority():
    """Negative: presentation OID selectors must not be classified as F1 AUTHORITY."""
    data = _load()
    by_id = {r["id"]: r for r in data["residuals"]}
    item = by_id["operationIdContains_column_labels"]
    assert item["status"] == "F2"
    assert item["f1Target"] == "OUT_OF_SCOPE_F2"


def test_f1_inventory_pre_cutover_has_authority_residuals():
    """Pre-F1 freeze: selection residuals still marked AUTHORITY (gate for later E*.S*)."""
    data = _load()
    authority = [
        r
        for r in data["residuals"]
        if r.get("status") in {"AUTHORITY", "AUTHORITY_PARTIAL"}
    ]
    assert len(authority) >= 4
    assert data.get("epic") == "F1"
    assert data.get("step") == "E0.S1"
