"""E8.S1 — freeze: inventário residual skills/help (contagens HEAD)."""

from __future__ import annotations

import json
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_SKILLS = _ROOT / "app/content/pt-BR/skills/catalog.json"
_FEATURES = _ROOT / "app/content/pt-BR/assistant/features_catalog.json"
_CAPABILITIES = _ROOT / "app/content/pt-BR/assistant/capabilities.json"
_REGISTRY = _ROOT / "app/content/pt-BR/assistant/capability_registry.json"
_EAR = _ROOT / "app/content/pt-BR/assistant/external_action_responses.json"

# Frozen 2026-09-10 — E8.S1 inventory-only (sem mutação de conteúdo).
_FREEZE = {
    "skills_total": 7,
    "execution_path_hint_pathish": 0,
    "execution_derived_key": 1,
    "features_total": 21,
    "features_with_path_required_actions": 12,
    "required_action_path_tokens": 26,
    "capabilities_http_method_path_mentions": 8,
    "capability_registry_route_hints": 0,
    "ear_action_selection_keys": 61,
}

_PATHISH_HINT = re.compile(
    r"(?i)^(?:GET|POST|PUT|PATCH|DELETE)\s+/|^/[A-Za-z0-9_{}/.-]+$"
)
_HTTP_METHOD_PATH = re.compile(
    r"(?i)\b(?:GET|POST|PUT|PATCH|DELETE)\s+/[A-Za-z0-9_{}/.-]+"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _walk_strings(node: object):
    if isinstance(node, dict):
        for value in node.values():
            yield from _walk_strings(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_strings(item)
    elif isinstance(node, str):
        yield node


def test_e8_s1_skills_pathish_hints_frozen():
    catalog = _load(_SKILLS)
    skills = catalog.get("skills") or []
    assert len(skills) == _FREEZE["skills_total"]

    pathish = 0
    derived = 0
    for skill in skills:
        assert isinstance(skill, dict)
        hint = str(skill.get("executionPathHint") or "").strip()
        if hint and _PATHISH_HINT.match(hint):
            pathish += 1
        if skill.get("executionDerivedKey"):
            derived += 1
        # KEEP R08-02 — policy editorial permanece.
        assert "key" in skill
        assert "policyFile" in skill or skill.get("key")

    assert pathish == _FREEZE["execution_path_hint_pathish"]
    assert derived == _FREEZE["execution_derived_key"]


def test_e8_s1_features_required_actions_path_tokens_frozen():
    catalog = _load(_FEATURES)
    features = catalog.get("features") or []
    if isinstance(features, dict):
        features = list(features.values())
    assert len(features) == _FREEZE["features_total"]

    with_path = 0
    tokens: list[str] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        required = feature.get("requiredActions") or []
        path_tokens = [
            str(token).strip()
            for token in required
            if isinstance(token, str) and str(token).strip().startswith("/")
        ]
        if path_tokens:
            with_path += 1
            tokens.extend(path_tokens)

    assert with_path == _FREEZE["features_with_path_required_actions"]
    assert len(tokens) == _FREEZE["required_action_path_tokens"]


def test_e8_s1_capabilities_http_mentions_and_dead_route_hints():
    capabilities = _load(_CAPABILITIES)
    mentions = 0
    for text in _walk_strings(capabilities):
        mentions += len(_HTTP_METHOD_PATH.findall(text))
    assert mentions == _FREEZE["capabilities_http_method_path_mentions"]

    registry = _load(_REGISTRY)
    blob = json.dumps(registry, ensure_ascii=False)
    assert blob.count("routeHints") == _FREEZE["capability_registry_route_hints"]
    assert "pathRules" not in registry


def test_e8_s1_ear_action_selection_residual_flagged():
    """EAR actionSelection é residual LIVE → E8.S4 (não limpar em S1)."""

    ear = _load(_EAR)
    selection = ear.get("actionSelection") or {}
    assert isinstance(selection, dict)
    assert len(selection) == _FREEZE["ear_action_selection_keys"]
