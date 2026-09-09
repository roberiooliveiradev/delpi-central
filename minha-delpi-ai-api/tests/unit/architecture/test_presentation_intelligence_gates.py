"""Architecture gates — Presentation Intelligence v1."""

from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_REPO = _ROOT.parent
_DOMAIN = _ROOT / "app/domain"
_MFE_CHAT_TYPES = (
    _REPO
    / "plugins/minha-delpi-chat/src/data/api/chatTypes.ts"
)


def _presentation_domain_paths() -> list[Path]:
    patterns = (
        "presentation_*.py",
        "chat_presentation_*.py",
        "chat_field_label_*.py",
        "chat_chart_type_selection_service.py",
    )
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend((_DOMAIN / "services").rglob(pattern))
        paths.extend((_DOMAIN / "entities").rglob(pattern))
    return sorted({path.resolve() for path in paths if path.is_file()})


def test_presentation_domain_does_not_import_application():
    violations: list[str] = []
    for path in _presentation_domain_paths():
        text = path.read_text(encoding="utf-8")
        if "app.application" in text:
            violations.append(str(path.relative_to(_ROOT)))
    assert violations == [], f"domain presentation leaked application imports: {violations}"


def test_presentation_spec_not_consumed_by_mfe():
    mfe_root = _REPO / "plugins/minha-delpi-chat/src"
    hits: list[str] = []
    for path in list(mfe_root.rglob("*.ts")) + list(mfe_root.rglob("*.tsx")):
        text = path.read_text(encoding="utf-8")
        if "presentationSpec" in text or "PresentationSpec" in text:
            hits.append(str(path.relative_to(_REPO)))
    assert hits == [], f"MFE must not consume PresentationSpec: {hits}"


def test_supported_marks_are_covered_by_mfe_chart_types():
    from app.domain.entities.presentation_spec import SUPPORTED_MARKS

    text = _MFE_CHAT_TYPES.read_text(encoding="utf-8")
    # Extract chartType union members from chatTypes.ts
    block = re.search(r"chartType:\s*((?:\n\s*\|[^\n]+)+)", text)
    assert block, "chartType union not found in chatTypes.ts"
    mfe_types = {
        match.group(1)
        for match in re.finditer(r'\|\s*"([a-z_]+)"', block.group(1))
    }
    missing = sorted(SUPPORTED_MARKS - mfe_types)
    assert missing == [], f"marks missing in MFE chatTypes: {missing}"


def test_presentation_intent_properties_match_planner_json():
    import json

    from app.domain.entities.presentation_spec import PRESENTATION_INTENT_JSON_SCHEMA

    path = _ROOT / "app/content/pt-BR/assistant/openapi_tool_routing.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    planner_props = (
        payload.get("planner", {})
        .get("schema", {})
        .get("properties", {})
        .get("presentationIntent", {})
        .get("properties", {})
    )
    python_props = set(PRESENTATION_INTENT_JSON_SCHEMA["properties"].keys())
    json_props = set(planner_props.keys())
    assert python_props == json_props, {
        "only_in_python": sorted(python_props - json_props),
        "only_in_json": sorted(json_props - python_props),
    }
