"""E9.S4 — gate de inventário: shadows críticos com owner + reason fields."""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_INVENTORY = (
    _ROOT / "tests/fixtures/intelligence_baseline/e9_s4_shadow_divergence_inventory.json"
)

_REQUIRED_IDS = {
    "registrySelectionShadow",
    "productSelectionShadow",
    "turnUnderstandingAuthorityShadow",
    "parameterStrategyShadow",
    "recommendationDualRun",
    "followUpRoutingAuthorityShadow",
}


def _load() -> dict:
    return json.loads(_INVENTORY.read_text(encoding="utf-8"))


def test_e9_s4_inventory_covers_critical_shadows():
    data = _load()
    shadows = data.get("shadows") or []
    ids = {str(item.get("id") or "") for item in shadows}
    assert _REQUIRED_IDS.issubset(ids)
    assert len(shadows) >= 6


def test_e9_s4_each_shadow_has_owner_module_and_reason_fields():
    data = _load()
    for shadow in data["shadows"]:
        assert str(shadow.get("owner") or "").strip(), shadow.get("id")
        assert str(shadow.get("module") or "").strip(), shadow.get("id")
        module = _ROOT / str(shadow["module"])
        assert module.is_file(), shadow["module"]
        assert shadow.get("sideEffects") is False, shadow.get("id")
        reasons = shadow.get("reasonFields") or []
        assert isinstance(reasons, list) and len(reasons) >= 1, shadow.get("id")
        signals = shadow.get("divergenceSignals") or []
        assert signals, shadow.get("id")
        evidence = str(shadow.get("evidence") or "")
        assert evidence.startswith("docs/roadmap/llm-json-decoupling/evidence/")
        assert (_ROOT / evidence).is_file(), evidence


def test_e9_s4_divergence_payload_requires_explainability():
    """Positive/negative: divergência exige reasonFields presentes no payload."""

    def explainable(payload: dict, reason_fields: list[str], diverged: bool) -> bool:
        if not diverged:
            return True
        return any(
            field in payload and payload.get(field) not in (None, "", [], {})
            for field in reason_fields
        )

    # Positive: agree=false com campos de razão
    assert explainable(
        {"agree": False, "legacyActionId": "a", "candidateTopIds": ["b"]},
        ["legacyActionId", "candidateTopIds", "error"],
        diverged=True,
    )
    # Sibling: agree=true não exige razão
    assert explainable({"agree": True}, ["error"], diverged=False)
    # Negative: diverge sem razão
    assert not explainable({"agree": False}, ["error", "onlyInCandidate"], diverged=True)
