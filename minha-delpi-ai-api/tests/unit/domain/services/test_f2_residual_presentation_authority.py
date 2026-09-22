"""F2 residual search: presentation path authority must stay retired/fallback."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_APP = _ROOT / "app"
_CONTENT = _APP / "content" / "pt-BR" / "assistant"
_INVENTORY = (
    _ROOT
    / "tests/fixtures/intelligence_baseline/f2_presentation_authority_inventory.json"
)
_DETECTION = (
    _APP
    / "domain/services/external_actions/presenters/kpi_chart/kpi_chart_detection_service.py"
)
_CONSTANTS = (
    _APP
    / "domain/services/external_actions/presenters/kpi_chart/kpi_chart_constants.py"
)
_PROFILE = (
    _APP / "domain/services/chat_operational_response_profile_service.py"
)
_COLUMN_LABELS = (
    _APP / "domain/services/external_actions/external_action_column_label_service.py"
)


def test_f2_inventory_authority_items_retired_or_fallback():
    payload = json.loads(_INVENTORY.read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in payload["items"]}

    assert by_id["kpi_path_token_detection"]["postStatus"] == "RETIRED"
    assert by_id["no_chart_path_fragments"]["postStatus"] == "RETIRED"
    assert by_id["column_labels_operationIdContains_on_path"]["postStatus"] == "RETIRED"
    assert by_id["sql_presentation_path_before_payload"]["postStatus"] == "RETIRED"
    assert by_id["entityPathHints"]["postStatus"] == "FALLBACK"


def test_f2_kpi_detection_has_no_path_token_authority():
    source = _DETECTION.read_text(encoding="utf-8")
    assert "kpi_paths" not in source
    assert "any(token in path" not in source
    assert "token in path for token" not in source


def test_f2_no_chart_paths_tombstone_empty():
    source = _CONSTANTS.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        targets: list[ast.expr] = []
        value = None
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
            value = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
            value = node.value
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id == "NO_CHART_PATHS":
                assert isinstance(value, ast.Tuple)
                assert len(value.elts) == 0
                return
    raise AssertionError("NO_CHART_PATHS not found")


def test_f2_is_no_chart_route_is_entity_only():
    source = _PROFILE.read_text(encoding="utf-8")
    match = re.search(
        r"def is_no_chart_route\(.*?\n(?:.*?\n)*?        return .+\n",
        source,
    )
    assert match, "is_no_chart_route not found"
    body = match.group(0)
    assert "is_no_chart_entity" in body
    assert "/structure" not in body
    assert "/suppliers" not in body
    assert "fragment in lowered" not in body


def test_f2_column_labels_oid_not_matched_against_path():
    source = _COLUMN_LABELS.read_text(encoding="utf-8")
    match = re.search(
        r"def _profile_matches\(.*?\n(?:.*?\n)*?        return False\n",
        source,
    )
    assert match, "_profile_matches not found"
    body = match.group(0)
    assert "operation_id" in body
    assert "lowered_path.replace" not in body
    assert "hay = lowered_path" not in body


def test_f2_sibling_column_labels_may_keep_operation_id_contains():
    """Sibling: operationIdContains may remain in JSON; matcher uses real OID."""
    payload = json.loads((_CONTENT / "column_labels.json").read_text(encoding="utf-8"))
    assert "operationIdContains" in json.dumps(payload)


def test_f2_entity_path_hints_fallback_meta():
    profiles = json.loads(
        (_CONTENT / "presentation_profiles.json").read_text(encoding="utf-8")
    )
    meta = profiles.get("cleanupMeta") or {}
    assert meta.get("entityPathHintsAuthority") is False
    assert meta.get("entityPathHintsFallbackOnlyAt") == "F2"
    assert len(profiles.get("entityPathHints") or {}) == 139


def test_f2_negative_path_alone_does_not_force_no_chart():
    from app.domain.services.chat_operational_response_profile_service import (
        ChatOperationalResponseProfileService,
    )

    assert not ChatOperationalResponseProfileService.is_no_chart_route(
        None,
        "/products/1/structure",
    )
    assert ChatOperationalResponseProfileService.is_no_chart_route(
        "product_structure",
        "/any/path",
    )


def test_f2_negative_path_alone_does_not_force_kpi():
    from app.domain.services.external_actions.presenters.kpi_chart.kpi_chart_detection_service import (
        ExternalActionKpiChartDetectionService,
    )

    class _Host:
        pass

    root = {"items": [{"code": "1", "name": "x"}], "total": 1}
    assert not ExternalActionKpiChartDetectionService.looks_like_kpi_response(
        _Host(),  # type: ignore[arg-type]
        root,
        "/supplies/cpv",
        entity=None,
    )
    # Sibling: payload shape still detects KPI without path tokens.
    assert ExternalActionKpiChartDetectionService.looks_like_kpi_response(
        _Host(),  # type: ignore[arg-type]
        {"value": 10, "percentage": 5},
        "/unrelated",
        entity=None,
    )


def test_f2_negative_oid_mismatch_skips_oid_gated_profile():
    from app.domain.services.external_actions.external_action_column_label_service import (
        ExternalActionColumnLabelService,
    )

    service = ExternalActionColumnLabelService()
    row = {"product_code": "1", "description": "PA"}
    assert (
        service.detect_table_profile(
            row,
            path="/products/1/stock",
            operation_id="get_product_stock",
        )
        == "stockProductPositions"
    )
    # Wrong OID must not use path as haystack to satisfy operationIdContains.
    assert (
        service.detect_table_profile(
            row,
            path="/products/1/stock",
            operation_id="get_product_sales",
        )
        != "stockProductPositions"
    )


def test_f2_positive_keys_only_without_oid():
    from app.domain.services.external_actions.external_action_column_label_service import (
        ExternalActionColumnLabelService,
    )

    service = ExternalActionColumnLabelService()
    row = {
        "branch": "01",
        "route_code": "01",
        "operation_code": "01",
        "operation_description": "EMBALAR",
    }
    assert service.detect_table_profile(row, path="/unrelated") == "guide"

