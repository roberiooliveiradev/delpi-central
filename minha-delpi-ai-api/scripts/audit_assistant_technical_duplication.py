"""Audit gate — bloqueia regressão de duplicação técnica em assistant/skills content (E8.S5)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_PATHISH_HINT = re.compile(
    r"(?i)^(?:GET|POST|PUT|PATCH|DELETE)\s+/|^/[A-Za-z0-9_{}/.-]+$"
)

# Bundles onde HTTP path em copy editorial é DOCUMENTATION_EXAMPLE (não authority).
_HTTP_COPY_ALLOWLIST_RELATIVE = frozenset(
    {
        "assistant/capabilities.json",
        "assistant/features_catalog.json",  # requiredActions path ainda LEGACY_FALLBACK
        "assistant/external_action_responses.json",  # PATH_COUPLED residual em actionSelection
        "assistant/operational_route_registry.json",
        "assistant/presentation_profiles.json",
        "assistant/api_route_domains.json",
    }
)


def audit_skills_catalog(catalog: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for skill in catalog.get("skills") or []:
        if not isinstance(skill, dict):
            continue
        key = str(skill.get("key") or "?")
        hint = str(skill.get("executionPathHint") or "").strip()
        if hint and _PATHISH_HINT.match(hint):
            errors.append(
                f"skills.catalog[{key}].executionPathHint path-like forbidden: {hint!r}"
            )
    return errors


def audit_capability_registry(registry: dict[str, Any]) -> list[str]:
    blob = json.dumps(registry, ensure_ascii=False)
    if "routeHints" in blob:
        return ["capability_registry must not contain routeHints (E4/E8)"]
    if "pathRules" in registry:
        return ["capability_registry must not contain pathRules"]
    return []


def audit_ear_ownership(ear: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    selection = ear.get("actionSelection") or {}
    if not isinstance(selection, dict):
        return ["external_action_responses.actionSelection missing"]

    if "routeClarification" in selection:
        errors.append(
            "actionSelection.routeClarification must live under actionSelectionCopy"
        )
    if "refinementFallbackMessages" in selection:
        errors.append(
            "actionSelection.refinementFallbackMessages must live under actionSelectionCopy"
        )

    copy = ear.get("actionSelectionCopy") or {}
    if not isinstance(copy, dict):
        errors.append("actionSelectionCopy missing after E8.S4")
    else:
        if not isinstance(copy.get("routeClarification"), dict):
            errors.append("actionSelectionCopy.routeClarification missing")
        if not isinstance(copy.get("refinementFallbackMessages"), dict):
            errors.append("actionSelectionCopy.refinementFallbackMessages missing")

    for family in selection.get("emptyRivalRecommendations") or []:
        if isinstance(family, dict) and "suggestions" in family:
            errors.append(
                "emptyRivalRecommendations[].suggestions must live under "
                "actionSelectionCopy.emptyRivalSuggestions"
            )
            break

    return errors


def audit_content_tree(content_root: Path) -> list[str]:
    """Audita árvore `app/content/pt-BR` (skills + registry + EAR ownership)."""

    errors: list[str] = []
    skills_path = content_root / "skills" / "catalog.json"
    registry_path = content_root / "assistant" / "capability_registry.json"
    ear_path = content_root / "assistant" / "external_action_responses.json"

    if skills_path.is_file():
        errors.extend(audit_skills_catalog(json.loads(skills_path.read_text(encoding="utf-8"))))
    else:
        errors.append(f"missing {skills_path}")

    if registry_path.is_file():
        errors.extend(
            audit_capability_registry(json.loads(registry_path.read_text(encoding="utf-8")))
        )
    else:
        errors.append(f"missing {registry_path}")

    if ear_path.is_file():
        errors.extend(audit_ear_ownership(json.loads(ear_path.read_text(encoding="utf-8"))))
    else:
        errors.append(f"missing {ear_path}")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1] / "app" / "content" / "pt-BR"
    errors = audit_content_tree(root)
    if errors:
        print("CONTENT_AUDIT FAIL")
        for item in errors:
            print(f" - {item}")
        return 1
    print("CONTENT_AUDIT PASS")
    _ = _HTTP_COPY_ALLOWLIST_RELATIVE  # documented exceptions for future scanners
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
