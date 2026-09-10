"""E8.S5 — audit gate de duplicação técnica em assistant/skills content."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.audit_assistant_technical_duplication import (
    audit_capability_registry,
    audit_content_tree,
    audit_ear_ownership,
    audit_skills_catalog,
)

_ROOT = Path(__file__).resolve().parents[3]
_CONTENT = _ROOT / "app/content/pt-BR"


def test_e8_s5_head_content_passes_audit():
    """Positive: árvore HEAD atual passa o gate."""

    errors = audit_content_tree(_CONTENT)
    assert errors == [], errors


def test_e8_s5_negative_pathish_skill_hint_fails():
    """Negative: executionPathHint HTTP/path é bloqueado."""

    catalog = {
        "skills": [
            {
                "key": "bad",
                "executionPathHint": "POST /data/sql",
            }
        ]
    }
    errors = audit_skills_catalog(catalog)
    assert errors
    assert "path-like" in errors[0]


def test_e8_s5_negative_route_hints_fail():
    errors = audit_capability_registry({"routeHints": ["/x"]})
    assert errors


def test_e8_s5_sibling_ear_copy_must_not_return_to_action_selection():
    ear = json.loads(
        (_CONTENT / "assistant/external_action_responses.json").read_text(encoding="utf-8")
    )
    # Sibling: HEAD ok
    assert audit_ear_ownership(ear) == []
    # Negative mutate
    ear["actionSelection"]["routeClarification"] = {"x": "y"}
    errors = audit_ear_ownership(ear)
    assert any("routeClarification" in item for item in errors)
