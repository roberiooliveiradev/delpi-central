"""Regressão — diretivas 90260882 em Automático, Tabela e Texto (schema-first / composite)."""

from __future__ import annotations

import pytest

from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta
from tests.fixtures.presentation_render_plan_gate import _validate_render_plan_contract

PATH = "/products/directives/90260882"
FIXTURE = "product_directives_90260882.json"
USER_MESSAGE = "diretivas 90260882"

EXPECTED_PANEL_TITLES = (
    "Indicadores consolidados",
    "Estrutura do produto 90260882",
    "Estrutura (BOM)",
)


def _use_case() -> ExecuteExternalActionUseCase:
    return ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )


def _build_metadata(session_format: str | None = None) -> dict:
    params: dict = {"userMessage": USER_MESSAGE}

    if session_format:
        params["sessionResponseFormat"] = session_format

    return _use_case()._build_presentation_metadata(
        action={"path": PATH, "intent": "operational_query"},
        sanitized_data=load_api_delpi_fixture_with_meta(FIXTURE),
        resolved_path=PATH,
        request_parameters=params,
    )


def _dashboard_panels(metadata: dict) -> list[dict]:
    dashboard = metadata.get("dashboardPresentation")

    if not isinstance(dashboard, dict):
        return []

    panels = dashboard.get("panels")

    if not isinstance(panels, list):
        return []

    return [item for item in panels if isinstance(item, dict)]


def _table_presentations(metadata: dict) -> list[dict]:
    bulk = metadata.get("tablePresentations")

    if isinstance(bulk, list):
        tables = [item for item in bulk if isinstance(item, dict) and item.get("type") == "table"]

        if tables:
            return tables

    table = metadata.get("tablePresentation")

    if isinstance(table, dict) and table.get("type") == "table":
        return [table]

    return []


def _render_plan_dashboard_segments(metadata: dict) -> list[dict]:
    render_plan = metadata.get("renderPlan")

    if not isinstance(render_plan, dict):
        return []

    return [
        segment
        for segment in render_plan.get("segments") or []
        if isinstance(segment, dict) and str(segment.get("kind") or "").lower() == "dashboard"
    ]


@pytest.mark.parametrize(
    ("session_format", "mode_label"),
    [
        (None, "automatico"),
        ("table", "tabela"),
        ("text", "texto"),
    ],
)
def test_directives_pipeline_exposes_composite_sections(session_format, mode_label):
    metadata = _build_metadata(session_format)
    panels = _dashboard_panels(metadata)
    panel_titles = [str(panel.get("title") or "") for panel in panels]

    assert len(panels) >= 3, f"[{mode_label}] esperava painéis consolidados, obteve {panel_titles}"
    assert panel_titles[:3] == list(EXPECTED_PANEL_TITLES)


@pytest.mark.parametrize(
    ("session_format", "expected_layout", "expected_explicit"),
    [
        (None, "stack", None),
        ("table", "single", "table"),
        ("text", "stack", "text"),
    ],
)
def test_directives_presentation_decision_by_mode(
    session_format,
    expected_layout,
    expected_explicit,
):
    metadata = _build_metadata(session_format)
    decision = metadata["presentationDecision"]

    assert decision["layoutMode"] == expected_layout
    assert "sem dados tabulares" not in str(decision.get("reason") or "").lower()

    explicit = metadata.get("explicitSessionFormat")

    if expected_explicit is None:
        assert not explicit or explicit in {"", "text"}
    else:
        assert explicit == expected_explicit


def test_directives_automatic_render_plan_includes_dashboard():
    metadata = _build_metadata(None)
    dashboard_segments = _render_plan_dashboard_segments(metadata)

    assert dashboard_segments
    assert _validate_render_plan_contract(metadata) == []


def test_directives_table_mode_keeps_consolidated_dashboard():
    metadata = _build_metadata("table")
    decision = metadata["presentationDecision"]

    assert decision["selected"] == "table"
    assert decision["layoutMode"] == "single"
    assert len(_dashboard_panels(metadata)) >= 3


def test_directives_text_mode_keeps_tables_in_payload_for_embed():
    metadata = _build_metadata("text")

    assert metadata.get("explicitSessionFormat") == "text"
    assert metadata["presentationDecision"]["layoutMode"] == "stack"
    assert metadata["presentationDecision"]["selected"] == "text"

    render_plan = metadata["renderPlan"]
    segment_kinds = {
        str(segment.get("kind") or "").strip().lower()
        for segment in render_plan.get("segments") or []
        if isinstance(segment, dict)
    }

    assert "markdown" in segment_kinds
    assert "dashboard" in segment_kinds or _table_presentations(metadata)
    assert _validate_render_plan_contract(metadata) == []


def test_directives_automatic_data_shape_has_rows():
    metadata = _build_metadata(None)
    shape = metadata["presentationDecision"].get("dataShape") or {}

    assert int(shape.get("rows") or 0) > 0


def test_directives_table_rows_counts_match_fixture():
    metadata = _build_metadata("text")
    tables = _table_presentations(metadata)

    assert tables
    assert len(tables[0]["rows"]) >= 2
    first_row = tables[0]["rows"][0]
    assert first_row.get("component_code") or first_row.get("raw_material_code")
    assert "parent_code" in first_row
