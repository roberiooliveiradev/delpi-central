"""E9.S10 — legacy fallback residual explicado (offline)."""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_FOLLOW_UP = (
    _ROOT / "app/content/pt-BR/assistant/operational_follow_up_routing.json"
)
_SHADOW = (
    _ROOT
    / "tests/fixtures/intelligence_baseline/e9_s4_shadow_divergence_inventory.json"
)


def test_e9_s10_follow_up_terms_deleted_e9_s12a():
    """Positive: messageSegmentTerms removidos; authority = follow_up_type."""
    doc = json.loads(_FOLLOW_UP.read_text(encoding="utf-8"))
    shadow = doc.get("authorityShadow") or {}
    assert shadow.get("cutoverEnabled") is True
    assert shadow.get("messageSegmentTermsRole") == "removed"
    assert shadow.get("deleteDeferredToWaveH") is False
    assert shadow.get("messageSegmentTermsDeletedAt") == "E9.S12.A"
    types = doc.get("followUpTypes") or {}
    assert not any(
        isinstance(v, dict) and (v.get("messageSegmentTerms") or [])
        for v in types.values()
    )


def test_e9_s10_recommendation_queries_legacy_fallback_role():
    """Sibling: recommendationQueries não é authority primária (legado residual)."""
    producer = (
        _ROOT
        / "app/domain/services/chat_contextual_recommendation_producer_service.py"
    )
    assert producer.is_file()
    text = producer.read_text(encoding="utf-8")
    assert "LEGACY_FALLBACK" in text or "legacy" in text.lower()
    assert "produce_with_dual_run" in text


def test_e9_s10_negative_remaining_residuals_still_gated():
    """Negative: DELETE follow-up ≠ liberar registry markers/strategy/TU."""
    shadows = json.loads(_SHADOW.read_text(encoding="utf-8"))
    ids = {s["id"] for s in shadows.get("shadows") or []}
    assert "recommendationDualRun" in ids
    assert "followUpRoutingAuthorityShadow" in ids
    gates = json.loads(
        (
            _ROOT / "tests/fixtures/intelligence_baseline/e9_s6_cleanup_gates.json"
        ).read_text(encoding="utf-8")
    )
    assert gates.get("deleteAuthorized") is False
    by_id = {c["id"]: c for c in gates.get("deleteCandidates") or []}
    assert by_id["turn_understanding_heuristics_json"]["status"] == "BLOCKED"
    assert by_id["registry_path_markers"]["status"] == "DELETED"
    assert by_id["registry_parameter_strategy_fields"]["status"] == "DELETED"
