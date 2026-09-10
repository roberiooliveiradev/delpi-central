"""E8.S2 — skill catalog: hints path-like → capability keys neutras."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.skills.chat_skill_registry import ChatSkillRegistry

configure_domain_infrastructure_ports()

_ROOT = Path(__file__).resolve().parents[4]
_SKILLS = _ROOT / "app/content/pt-BR/skills/catalog.json"

_PATHISH_HINT = re.compile(
    r"(?i)^(?:GET|POST|PUT|PATCH|DELETE)\s+/|^/[A-Za-z0-9_{}/.-]+$"
)
_HTTP_IN_HINT = re.compile(r"(?i)\b(?:GET|POST|PUT|PATCH|DELETE)\s+/")

_EXPECTED_HINTS = {
    "company-knowledge": "search_knowledge_base",
    "sql": "sql_execution",
    "technical-description-delpi": "Normas_Tecnicas_DELPI + Intermediate Product Codes",
    "drawing-analysis-delpi": "product_analyser",
    "document-vision-delpi": "document_vision",
    "quality-action-plans-delpi": "quality_action_plans",
    "tv-dashboard-copilot": "tv_dashboard_copilot",
}


def _catalog_skills() -> list[dict]:
    return list(json.loads(_SKILLS.read_text(encoding="utf-8")).get("skills") or [])


def test_e8_s2_no_pathish_execution_path_hints():
    """Positive: zero hints HTTP/path; capability keys neutras."""

    for skill in _catalog_skills():
        key = str(skill.get("key") or "")
        hint = str(skill.get("executionPathHint") or "").strip()
        assert hint, f"skill {key} sem executionPathHint"
        assert not _PATHISH_HINT.match(hint), (key, hint)
        assert not _HTTP_IN_HINT.search(hint), (key, hint)
        if key in _EXPECTED_HINTS:
            assert hint == _EXPECTED_HINTS[key]


def test_e8_s2_sql_derived_key_and_policy_preserved():
    """Sibling: sql mantém derived key + policy; hint não é endpoint."""

    sql = next(s for s in _catalog_skills() if s.get("key") == "sql")
    assert sql.get("executionPathHint") == "sql_execution"
    assert sql.get("executionDerivedKey") == "sqlExecutionAvailable"
    assert sql.get("policyFile") == "sql-assistant-skill.md"
    assert "POST /data/sql" not in str(sql.get("description") or "")


def test_e8_s2_enablement_ignores_hint_text():
    """Negative: binding enabled + derived SQL usa actions, não o texto do hint."""

    metadata = ChatSkillRegistry.set_enabled({}, "sql", True)
    bindings = ChatSkillRegistry.list_agent_bindings(
        agent_metadata=metadata,
        allowed_action_ids=[],
        has_agent=True,
    )
    sql = next(item for item in bindings if item.get("skillKey") == "sql")
    assert sql.get("enabled") is True
    assert sql.get("executionHint") == "sql_execution"
    assert (sql.get("derived") or {}).get("sqlExecutionAvailable") is False
