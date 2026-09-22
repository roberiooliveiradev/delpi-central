"""F5 — CI residual: anti-reintroduction of OpenAPI-first anti-patterns."""

from __future__ import annotations

import json
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_APP = _ROOT / "app"
_CONTENT = _APP / "content" / "pt-BR" / "assistant"
_INVENTORY = (
    _ROOT
    / "tests/fixtures/intelligence_baseline/f5_ci_anti_reintroduction_inventory.json"
)


def test_f5_inventory_locked():
    payload = json.loads(_INVENTORY.read_text(encoding="utf-8"))
    assert payload["epic"] == "F5"
    assert payload.get("gateMode") == "fail_closed"


def test_f5_selection_content_has_no_path_oid_authority_keys():
    # Selection authority surfaces (not UX intent vocabulary).
    for name in (
        "operational_group_by_refinement.json",
        "operational_route_registry.json",
    ):
        blob = (_CONTENT / name).read_text(encoding="utf-8")
        for key in (
            '"pathContains"',
            '"pathContainsFromKey"',
            '"customPredicate"',
            '"preferredRouteId"',
        ):
            assert key not in blob, (name, key)

    # Sibling: UX intent vocabulary may keep customPredicate language markers.
    responses = (_CONTENT / "external_action_responses.json").read_text(encoding="utf-8")
    assert '"pathContains"' not in responses
    assert '"preferredRouteId"' not in responses


def test_f5_kpi_detection_has_no_path_token_list():
    source = (
        _APP
        / "domain/services/external_actions/presenters/kpi_chart/kpi_chart_detection_service.py"
    ).read_text(encoding="utf-8")
    assert "kpi_paths" not in source
    assert "token in path for token" not in source


def test_f5_write_confirmation_gates_present():
    confirm = (
        _APP / "domain/services/chat_write_confirmation_service.py"
    ).read_text(encoding="utf-8")
    assert "should_block_execution" in confirm
    assert "is_parallel_safe_read" in confirm
    executor = (
        _APP / "application/use_cases/execute_external_action_use_case.py"
    ).read_text(encoding="utf-8")
    assert "_confirmation_block_result" in executor


def test_f5_prioritization_apply_remains_noop():
    source = (
        _APP
        / "application/services/external_actions/external_action_candidate_prioritization_service.py"
    ).read_text(encoding="utf-8")
    match = re.search(r"def apply\([\s\S]*?return list\(candidates\)", source)
    assert match, "apply() must remain catalog-order noop"
    body = match.group(0)
    assert "pathContains" not in body
    assert "operationIdContains" not in body


def test_f5_sibling_column_labels_may_keep_operation_id_contains():
    blob = (_CONTENT / "column_labels.json").read_text(encoding="utf-8")
    assert "operationIdContains" in blob
