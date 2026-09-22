"""Handoff TV — content bundle sem catálogo de ops embutido."""

from __future__ import annotations

import json
from pathlib import Path

HANDOFF_PATH = (
    Path(__file__).resolve().parents[4]
    / "app"
    / "content"
    / "pt-BR"
    / "assistant"
    / "tv_dashboard_handoff.json"
)


def test_handoff_json_has_no_embedded_capabilities_or_allowed_ops():
    raw = HANDOFF_PATH.read_text(encoding="utf-8")
    doc = json.loads(raw)
    assert "capabilities" not in doc
    assert "allowedOps" not in doc
    assert "redirectToVista" in doc
    forbidden_snippets = (
        '"upsert_data_source"',
        '"add_slide_from_preset"',
        '"create_playlist"',
        '"upsert_block"',
    )
    for snippet in forbidden_snippets:
        assert snippet not in raw, f"handoff não deve listar op {snippet}"


def test_legacy_copilot_intent_json_absent():
    legacy = HANDOFF_PATH.parent / "tv_dashboard_copilot_intent.json"
    assert not legacy.exists()
