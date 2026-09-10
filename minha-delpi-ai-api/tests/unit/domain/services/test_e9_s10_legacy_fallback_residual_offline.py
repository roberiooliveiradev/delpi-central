"""E9.S10 — legacy fallback residual explicado (offline)."""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_FOLLOW_UP = (
    _ROOT / "app/content/pt-BR/assistant/operational_follow_up_routing.json"
)
_EAR = _ROOT / "app/content/pt-BR/assistant/external_action_responses.json"
_SHADOW = (
    _ROOT
    / "tests/fixtures/intelligence_baseline/e9_s4_shadow_divergence_inventory.json"
)


def test_e9_s10_follow_up_terms_are_observer_not_authority():
    """Positive: messageSegmentTerms residual marcado observer + delete deferred."""
    doc = json.loads(_FOLLOW_UP.read_text(encoding="utf-8"))
    shadow = doc.get("authorityShadow") or {}
    assert shadow.get("cutoverEnabled") is True
    assert shadow.get("messageSegmentTermsRole") == "observer"
    assert shadow.get("deleteDeferredToWaveH") is True
    # residual ainda presente (explicado)
    types = doc.get("followUpTypes") or {}
    assert any(
        isinstance(v, dict) and (v.get("messageSegmentTerms") or [])
        for v in types.values()
    )


def test_e9_s10_recommendation_queries_legacy_fallback_role():
    """Sibling: recommendationQueries não é authority primária (legado residual)."""
    # Conteúdo pode viver em recommendation_queries / EAR — checar README/content
    # via presence of dual-run producer module (authority candidate-first).
    producer = (
        _ROOT
        / "app/domain/services/chat_contextual_recommendation_producer_service.py"
    )
    assert producer.is_file()
    text = producer.read_text(encoding="utf-8")
    assert "LEGACY_FALLBACK" in text or "legacy" in text.lower()
    assert "produce_with_dual_run" in text


def test_e9_s10_negative_legacy_residual_still_inventoried_for_delete_gate():
    """Negative: residual explicado ≠ autorizado a DELETE (E9.S6 ainda bloqueia)."""
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
