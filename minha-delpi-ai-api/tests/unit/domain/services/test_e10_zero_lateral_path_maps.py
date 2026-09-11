"""E10 — zero lateral path maps in assistant content (object keys)."""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_ASSISTANT = _ROOT / "app/content/pt-BR/assistant"

_FORBIDDEN_KEYS = frozenset(
    {
        "pathMarkers",
        "excludePathMarkers",
        "pathMarkersKey",
        "pathToken",
        "pathContains",
        "pathExactEnd",
        "pathSuffix",
        "pathContainsFromKey",
        "pathRules",
    }
)


def _forbidden_key_hits() -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}

    for path in sorted(_ASSISTANT.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        found: list[str] = []

        def walk(node: object, cursor: str = "$") -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    key_s = str(key)
                    if key_s in _FORBIDDEN_KEYS or "PathMarkers" in key_s:
                        found.append(f"{cursor}.{key_s}")
                    walk(value, f"{cursor}.{key_s}")
            elif isinstance(node, list):
                for index, item in enumerate(node):
                    walk(item, f"{cursor}[{index}]")

        walk(payload)
        if found:
            hits[str(path.relative_to(_ASSISTANT))] = found

    return hits


def test_e10_assistant_content_has_zero_lateral_path_map_keys():
    """Positive: content JSON não carrega mapa lateral por path."""
    hits = _forbidden_key_hits()
    assert hits == {}, hits


def test_e10_api_route_domains_has_labels_without_path_maps():
    """Sibling: domains restam como label/method + parameterStrategies."""
    data = json.loads(
        (_ASSISTANT / "api_route_domains.json").read_text(encoding="utf-8")
    )
    domains = data.get("domains") or {}
    assert "product" in domains
    assert "parameterStrategies" in data
    for domain_id, config in domains.items():
        assert isinstance(config, dict), domain_id
        assert "pathMarkers" not in config
        assert "excludePathMarkers" not in config
        assert "label" in config


def test_e10_openapi_tool_routing_still_lists_pathmarkers_as_forbidden_pattern():
    """Negative: gate string 'pathMarkers' em forbiddenPathSubstringPatterns é permitido."""
    data = json.loads(
        (_ASSISTANT / "openapi_tool_routing.json").read_text(encoding="utf-8")
    )
    patterns = (data.get("gate") or {}).get("forbiddenPathSubstringPatterns") or []
    assert any("pathMarkers" in str(item) for item in patterns)
