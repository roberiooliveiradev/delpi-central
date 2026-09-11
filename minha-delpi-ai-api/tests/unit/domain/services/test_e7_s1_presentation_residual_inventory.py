"""E7.S1 — freeze: inventário residual de presentation (contagens HEAD)."""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_ASSISTANT = _ROOT / "app/content/pt-BR/assistant"
_PROFILES = _ASSISTANT / "presentation_profiles.json"
_COLUMNS = _ASSISTANT / "column_labels.json"
_PRESENTER = _ASSISTANT / "presenter_content.json"

# Frozen 2026-09-11 — Onda I remove pathRules / pathContains laterais.
_FREEZE = {
    "pathRules": 0,
    "entityProfiles": 34,
    "entityTableProfiles": 18,
    "entityPathHints": 139,
    "tableProfilesWithPathContains": 0,
    "tableProfilesTotal": 76,
    "openapiShapeDefaults": 9,
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_e7_s1_path_entity_residual_counts_frozen():
    profiles = _load(_PROFILES)
    columns = _load(_COLUMNS)

    assert len(profiles.get("pathRules") or []) == _FREEZE["pathRules"]
    assert len(profiles.get("entityProfiles") or {}) == _FREEZE["entityProfiles"]
    assert len(profiles.get("entityTableProfiles") or {}) == _FREEZE["entityTableProfiles"]
    assert len(profiles.get("entityPathHints") or {}) == _FREEZE["entityPathHints"]

    shape_defaults = profiles.get("openapiShapeDefaults") or {}
    assert len(shape_defaults) == _FREEZE["openapiShapeDefaults"]
    assert {
        "scalar",
        "list",
        "paged_list",
        "hierarchy",
        "composite_analysis",
        "document_export",
        "unknown",
    }.issubset(set(shape_defaults.keys()))

    table_profiles = columns.get("tableProfiles") or {}
    assert len(table_profiles) == _FREEZE["tableProfilesTotal"]
    with_path = 0
    for profile in table_profiles.values():
        if not isinstance(profile, dict):
            continue
        detect = profile.get("detect") or {}
        if isinstance(detect, dict) and detect.get("pathContains"):
            with_path += 1
    assert with_path == _FREEZE["tableProfilesWithPathContains"]


def test_e7_s1_dead_orphans_flagged():
    profiles = _load(_PROFILES)
    presenter = _load(_PRESENTER)

    assert "pathEntityFallbacks" not in profiles
    entity_sets = profiles.get("entitySets") or {}
    migrated = entity_sets.get("schemaFirstMigratedProfiles") or []
    assert isinstance(migrated, list)
    assert len(migrated) >= 1  # E7.S4 popula ledger de cutovers
    # Órfão removido em E7.S4.
    assert "compositeVisualSpecs" not in presenter


def test_e7_s1_field_formats_policy_preserved():
    columns = _load(_COLUMNS)
    formats = columns.get("fieldFormats") or {}
    assert isinstance(formats, dict)
    assert len(formats) >= 50  # KEEP R07-02 — não migrar para LLM
