"""E5.S1 — F1 residual search: selection authority must stay retired."""

from __future__ import annotations

import json
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_APP = _ROOT / "app"
_CONTENT = _APP / "content" / "pt-BR" / "assistant"

# Presentation / F2 surfaces allowed to keep operationIdContains.
_F2_ALLOWLIST = {
    "column_labels.json",
}

# Cold admin / lint / generator may still mention OperationalRoute symbols.
_COLD_ADMIN_ALLOW_PATH_FRAGMENTS = (
    "/operational_route_suggestion_service.py",
    "/suggest_operational_routes_use_case.py",
    "/operational_route_registry_lint_service.py",
    "/operational_route_registry_generator_service.py",
    "/operational_route_narrative_service.py",
    "/scripts/",
)

_FORBIDDEN_CONTENT_KEYS = (
    "pathContains",
    "pathContainsFromKey",
    "operationIdContains",
    "operationIdContainsFromKey",
    "preferredRouteId",
)

_SELECTION_PY_PATTERNS = [
    (
        re.compile(r"select_operational_registry\s*\("),
        "select_operational_registry call",
        {
            "external_action_route_selection_service.py",  # tombstone body ok if returns None
        },
    ),
]


def _iter_py_files():
    for path in _APP.rglob("*.py"):
        text = str(path)
        if any(frag in text.replace("\\", "/") for frag in _COLD_ADMIN_ALLOW_PATH_FRAGMENTS):
            continue
        yield path


def test_f1_residual_registry_has_no_custom_predicate():
    payload = json.loads(
        (_CONTENT / "operational_route_registry.json").read_text(encoding="utf-8")
    )
    blob = json.dumps(payload)
    assert '"customPredicate"' not in blob
    assert payload.get("refinementVocabulary", {}).get("paginatedPathFragments") in (
        [],
        None,
    )


def test_f1_residual_follow_up_has_no_route_sot():
    payload = json.loads(
        (_CONTENT / "operational_follow_up_routing.json").read_text(encoding="utf-8")
    )
    for cfg in (payload.get("followUpTypes") or {}).values():
        if not isinstance(cfg, dict):
            continue
        assert "routeSegment" not in cfg
        assert "preferredRouteId" not in cfg


def test_f1_residual_selection_content_has_no_path_oid_selectors():
    """Positive: selection JSON without path/OID authority keys."""
    for name in (
        "external_action_responses.json",
        "operational_group_by_refinement.json",
    ):
        payload = json.loads((_CONTENT / name).read_text(encoding="utf-8"))
        blob = json.dumps(payload)
        for key in _FORBIDDEN_CONTENT_KEYS:
            assert f'"{key}"' not in blob, (name, key)


def test_f1_residual_sibling_negative_column_labels_may_keep_oid():
    """Negative/sibling: presentation column_labels may keep operationIdContains (F2)."""
    payload = json.loads((_CONTENT / "column_labels.json").read_text(encoding="utf-8"))
    blob = json.dumps(payload)
    assert "operationIdContains" in blob


def test_f1_residual_product_cutover_has_no_legacy_select_call():
    source = (
        _APP
        / "application/services/external_actions/external_action_selection_service.py"
    ).read_text(encoding="utf-8")
    # Cutover product path must not call legacy product select.
    assert "legacyRemovedAt" in source
    assert source.count("_select_product_action(") <= 2  # method def + refinement helper only


def test_f1_residual_select_operational_registry_is_tombstone():
    source = (
        _APP
        / "application/services/external_actions/external_action_route_selection_service.py"
    ).read_text(encoding="utf-8")
    assert "tombstone" in source.lower() or "F1" in source
    # Method must return None without calling operational route select.
    assert "return None" in source
    assert "self._operational_route.select(" not in source.split(
        "def select_operational_registry"
    )[1].split("def ")[0]


def test_f1_residual_prioritization_apply_is_noop_authority():
    source = (
        _APP
        / "application/services/external_actions/external_action_candidate_prioritization_service.py"
    ).read_text(encoding="utf-8")
    # apply() must not read pathContains/operationIdContains for authority.
    apply_block = source.split("def apply(")[1].split("def ")[0]
    assert "pathContains" not in apply_block
    assert "operationIdContains" not in apply_block
    assert "siblingDisambiguation" not in apply_block
