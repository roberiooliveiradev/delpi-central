"""E9.S5 — inventário de cutover/canary canônico + rollback observável."""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_INVENTORY = (
    _ROOT / "tests/fixtures/intelligence_baseline/e9_s5_canary_cutover_inventory.json"
)

_REQUIRED_IDS = {
    "registrySelectionShadow",
    "productSelectionShadow",
    "parameterStrategyShadow",
    "followUpRoutingAuthorityShadow",
    "turnUnderstandingShadow",
    "productFamilyAuthorityShadow",
    "taskPlannerEnabled",
    "departmentCompositionCutover",
    "entityEnrichmentCutover",
    "recommendationDualRun",
    "openapiPlannerMode",
    "presentationComposerCanary",
}


def _load() -> dict:
    return json.loads(_INVENTORY.read_text(encoding="utf-8"))


def _resolve_path(doc: dict, path: list[str]):
    cur: object = doc
    for key in path:
        assert isinstance(cur, dict), path
        assert key in cur, (path, key)
        cur = cur[key]
    return cur


def test_e9_s5_cohort_agent_canary_is_absent():
    data = _load()
    cohort = data.get("cohortAgentCanary") or {}
    assert cohort.get("status") == "ABSENT"
    assert str(cohort.get("note") or "").strip()


def test_e9_s5_inventory_covers_required_cutovers():
    data = _load()
    cutovers = data.get("cutovers") or []
    ids = {str(item.get("id") or "") for item in cutovers}
    assert _REQUIRED_IDS.issubset(ids)
    assert len(cutovers) >= 11


def test_e9_s5_each_cutover_has_owner_rollback_and_observability():
    data = _load()
    for item in data["cutovers"]:
        cid = item.get("id")
        assert str(item.get("owner") or "").strip(), cid
        assert str(item.get("rollbackHow") or "").strip(), cid
        assert str(item.get("observability") or "").strip(), cid
        assert str(item.get("moduleOwner") or "").strip(), cid
        module = _ROOT / str(item["moduleOwner"])
        assert module.is_file(), item["moduleOwner"]
        assert "flagReversible" in item, cid
        assert "liveL1L4Applicable" in item, cid
        evidence = str(item.get("evidence") or "")
        assert evidence, cid
        evidence_path = _ROOT / evidence
        assert evidence_path.exists(), evidence


def test_e9_s5_flag_reversible_controls_exist():
    """Positive: dials reversíveis apontam para content/env reais."""
    data = _load()
    reversible = [c for c in data["cutovers"] if c.get("flagReversible") is True]
    assert len(reversible) >= 4

    for item in reversible:
        kind = item.get("controlKind")
        if kind in ("content_json", "content_json_env"):
            surface = _ROOT / str(item["controlSurface"])
            assert surface.is_file(), item["id"]
            doc = json.loads(surface.read_text(encoding="utf-8"))
            value = _resolve_path(doc, list(item["controlPath"]))
            assert value is not None or value is False or value is True, item["id"]
        if kind in ("content_json_env", "env"):
            assert str(item.get("envOverride") or "").strip(), item["id"]


def test_e9_s5_non_reversible_are_explicit():
    """Negative/sibling: sem dial falso — legacy_removed / permanent / telemetry_only."""
    data = _load()
    for item in data["cutovers"]:
        if item.get("flagReversible") is True:
            continue
        kind = item.get("controlKind")
        assert kind in {
            "legacy_removed",
            "hardcoded_on",
            "telemetry_only",
            "content_json",  # parameterStrategy: dial existe mas não reativa legado
        }, (item.get("id"), kind)
        assert "LEGADO" in item["rollbackHow"] or "Sem flag" in item["rollbackHow"] or "Sem off" in item["rollbackHow"] or "RESTORE" in item["rollbackHow"].upper() or "restore" in item["rollbackHow"].lower() or "alteração de código" in item["rollbackHow"], item.get("id")


def test_e9_s5_no_fake_cohort_canary_surface():
    """Negative: inventário não declara cohort/agent dial inexistente."""
    data = _load()
    blob = json.dumps(data, ensure_ascii=False).lower()
    assert data["cohortAgentCanary"]["status"] == "ABSENT"
    # Não inventar campos de cohort binding
    for item in data["cutovers"]:
        assert "cohortAllowlist" not in item
        assert "agentAllowlist" not in item
    assert "cohortallowlist" not in blob
