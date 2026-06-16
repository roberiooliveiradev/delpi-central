"""Regressão — diretivas 90260882 em Automático, Tabela e Texto."""

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

EXPECTED_TABLE_TITLES = (
    "Estrutura do produto (BOM)",
    "Fornecedores por matéria-prima",
    "Última compra por matéria-prima",
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


def _table_presentations(metadata: dict) -> list[dict]:
    bulk = metadata.get("tablePresentations")

    if not isinstance(bulk, list):
        return []

    return [item for item in bulk if isinstance(item, dict) and item.get("type") == "table"]


def _render_plan_table_segments(metadata: dict) -> list[dict]:
    render_plan = metadata.get("renderPlan")

    if not isinstance(render_plan, dict):
        return []

    return [
        segment
        for segment in render_plan.get("segments") or []
        if isinstance(segment, dict) and str(segment.get("kind") or "").lower() == "table"
    ]


@pytest.mark.parametrize(
    ("session_format", "mode_label"),
    [
        (None, "automatico"),
        ("table", "tabela"),
        ("text", "texto"),
    ],
)
def test_directives_pipeline_three_tables_in_metadata(session_format, mode_label):
    metadata = _build_metadata(session_format)
    tables = _table_presentations(metadata)
    titles = [str(table.get("title") or "") for table in tables]

    assert len(tables) == 3, f"[{mode_label}] esperava 3 tabelas, obteve {len(tables)}: {titles}"
    assert titles == list(EXPECTED_TABLE_TITLES)


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


def test_directives_automatic_render_plan_includes_operational_tables():
    metadata = _build_metadata(None)
    table_segments = _render_plan_table_segments(metadata)

    assert any(
        segment.get("slot") == "operationalTables"
        and segment.get("source") == "tablePresentations"
        for segment in table_segments
    )
    assert _validate_render_plan_contract(metadata) == []


def test_directives_table_mode_render_plan_operational_tables():
    metadata = _build_metadata("table")
    decision = metadata["presentationDecision"]
    table_segments = _render_plan_table_segments(metadata)

    assert decision["selected"] == "table"
    assert decision["layoutMode"] == "single"
    assert table_segments == [
        {
            "kind": "table",
            "slot": "operationalTables",
            "source": "tablePresentations",
        },
    ]


def test_directives_text_mode_keeps_tables_in_payload_for_embed():
    metadata = _build_metadata("text")

    assert metadata.get("explicitSessionFormat") == "text"
    assert len(_table_presentations(metadata)) == 3
    assert metadata["presentationDecision"]["layoutMode"] == "stack"
    assert metadata["presentationDecision"]["selected"] == "text"

    render_plan = metadata["renderPlan"]
    segment_kinds = {
        str(segment.get("kind") or "").strip().lower()
        for segment in render_plan.get("segments") or []
        if isinstance(segment, dict)
    }

    assert "markdown" in segment_kinds
    # Payload mantém tabelas para o MFE embutir GFM no modo Texto (isExplicitTextSessionMode).
    assert _validate_render_plan_contract(metadata) == []


def test_directives_automatic_data_shape_has_rows():
    metadata = _build_metadata(None)
    shape = metadata["presentationDecision"].get("dataShape") or {}

    assert int(shape.get("rows") or 0) > 0


def test_directives_table_rows_counts_match_fixture():
    metadata = _build_metadata(None)
    tables = _table_presentations(metadata)

    assert len(tables[0]["rows"]) == 2
    assert tables[0]["rows"][0]["raw_material_code"] == "10080626"
    assert "parent_code" not in tables[0]["rows"][0]
    assert [column["key"] for column in tables[0]["columns"]][:2] == [
        "raw_material_code",
        "description",
    ]
    assert len(tables[1]["rows"]) == 3
    assert [column["key"] for column in tables[1]["columns"]][:2] == [
        "raw_material_code",
        "raw_material_description",
    ]
    assert len(tables[2]["rows"]) == 2
    assert [column["key"] for column in tables[2]["columns"]][:2] == [
        "raw_material_code",
        "description",
    ]
