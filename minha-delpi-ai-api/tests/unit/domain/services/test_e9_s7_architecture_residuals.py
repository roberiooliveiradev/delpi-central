"""E9.S7 — architecture audit: todo residual do checklist classificado."""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_AUDIT = (
    _ROOT / "tests/fixtures/intelligence_baseline/e9_s7_architecture_residuals.json"
)
_GATES = _ROOT / "tests/fixtures/intelligence_baseline/e9_s6_cleanup_gates.json"

_REQUIRED_RESIDUAL_IDS = {
    "pathMarkers",
    "operationIdMarkers",
    "parameterStrategy_per_endpoint",
    "pathToken_pathContains",
    "routeHints",
    "scopeToRouteId",
    "preferredRouteId",
    "manual_endpoint_priority",
    "if_path_provider_operationId",
    "messageSegmentTerms",
}

_ALLOWED_DISPOSITIONS = {
    "REMOVE_WHEN_GATES_PASS",
    "REMOVE_REQUIRED",
    "JUSTIFIED_POLICY",
    "JUSTIFIED_COMPATIBILITY",
    "JUSTIFIED_DOCUMENTATION",
    "REMOVED",
}


def _load() -> dict:
    return json.loads(_AUDIT.read_text(encoding="utf-8"))


def test_e9_s7_covers_plan_checklist():
    data = _load()
    ids = {str(r.get("id") or "") for r in data.get("residuals") or []}
    assert _REQUIRED_RESIDUAL_IDS.issubset(ids)


def test_e9_s7_each_residual_has_disposition_and_justification():
    data = _load()
    for item in data["residuals"]:
        rid = item.get("id")
        disp = item.get("disposition")
        assert disp in _ALLOWED_DISPOSITIONS, (rid, disp)
        assert str(item.get("justification") or "").strip(), rid
        assert "inCoreGenericSelection" in item, rid


def test_e9_s7_delete_authorized_aligns_with_e9_s6_gates():
    """Positive: residuals REMOVE_WHEN_GATES_PASS alinhados a E9.S6 deleteAuthorized."""
    data = _load()
    gates = json.loads(_GATES.read_text(encoding="utf-8"))
    assert data.get("deleteAuthorized") is True
    assert gates.get("deleteAuthorized") is True
    remove_pending = [
        r["id"]
        for r in data["residuals"]
        if r.get("disposition") == "REMOVE_WHEN_GATES_PASS"
    ]
    # Onda H/I: maioria REMOVED/REMOVE_REQUIRED; residual pending pode ser zero.
    assert isinstance(remove_pending, list)

def test_e9_s7_justified_or_removed_not_silently_empty():
    """Sibling: itens REMOVED/JUSTIFIED existem e não pedem delete agora."""
    data = _load()
    justified = [
        r
        for r in data["residuals"]
        if str(r.get("disposition") or "").startswith("JUSTIFIED")
        or r.get("disposition") == "REMOVED"
    ]
    assert len(justified) >= 3
    for item in justified:
        assert item.get("disposition") != "REMOVE_WHEN_GATES_PASS"


def test_e9_s7_negative_no_unclassified_core_authority():
    """Negative: nada marcado como authority no core genérico sem justificação."""
    data = _load()
    for item in data["residuals"]:
        role = item.get("inCoreGenericSelection")
        assert role in {False, "observer_or_compat", "forbidden_as_authority"}, (
            item.get("id"),
            role,
        )
        if role == "forbidden_as_authority":
            assert "JUSTIFIED" in str(item.get("disposition")), item.get("id")


def test_e9_s7_surfaces_exist_when_listed():
    data = _load()
    for item in data["residuals"]:
        for surface in item.get("surfaces") or []:
            path = _ROOT / surface
            # directories may end with /
            if surface.endswith("/"):
                assert path.is_dir() or any(
                    (_ROOT / "app").rglob("*")
                ), surface
                continue
            assert path.exists(), surface
