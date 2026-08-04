"""AP9 — a AI não embute catálogo de ops do TV Copilot."""

from __future__ import annotations

import json
from pathlib import Path

INTENT_PATH = (
    Path(__file__).resolve().parents[4]
    / "app"
    / "content"
    / "pt-BR"
    / "assistant"
    / "tv_dashboard_copilot_intent.json"
)

SKILL_PATH = (
    Path(__file__).resolve().parents[4]
    / "app"
    / "domain"
    / "prompt_policies"
    / "tv-dashboard-copilot-skill.md"
)


def test_intent_json_has_no_embedded_capabilities_or_allowed_ops():
    """Proibido sync --write AI←BFF: intent não carrega capabilities[] / allowedOps."""
    raw = INTENT_PATH.read_text(encoding="utf-8")
    doc = json.loads(raw)
    assert "capabilities" not in doc
    assert "allowedOps" not in doc
    # Nomes de ops de produto não devem figurar como catálogo embutido.
    forbidden_snippets = (
        '"upsert_data_source"',
        '"add_slide_from_preset"',
        '"create_playlist"',
        '"upsert_block"',
    )
    for snippet in forbidden_snippets:
        assert snippet not in raw, f"intent não deve listar op {snippet}"


def test_skill_md_does_not_enumerate_product_ops():
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "upsert_data_source" not in text
    assert "add_slide_from_preset" not in text
    assert "create_playlist" not in text
    assert "suggest-ops" in text or "catálogo" in text.lower() or "catalogo" in text.lower()
