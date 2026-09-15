"""TM-GPI-009 — gpt_get_catalog exposes canonical flowchart/BPMN catalog to TÉO."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from tm_app.application.gpt_actions.openapi_builder import (
    GPT_ACTIONS_OPERATION_IDS,
    build_gpt_actions_openapi,
    count_operations,
)
from tm_app.application.gpt_actions.registration_guide import build_registration_guide
from tm_app.domain.diagram.bpmn_mermaid_mapping import build_bpmn_catalog_for_api
from tm_app.domain.diagram.bpmn_node_catalog import EDGE_KINDS, NODE_TYPES
from tm_app.domain.diagram.flowchart_v1 import validate_flowchart_v1


def _catalog_via_http(tm_client):
    with (
        patch(
            "tm_app.application.gpt_actions.dispatch_service.FilialRepository"
        ) as filial_cls,
        patch(
            "tm_app.application.gpt_actions.dispatch_service.SetorRepository"
        ) as setor_cls,
        patch(
            "tm_app.application.gpt_actions.dispatch_service.ProcessoRepository"
        ) as proc_cls,
    ):
        filial_cls.return_value.list_for_options.return_value = [
            {"id": "01", "label": "SC"}
        ]
        setor_cls.return_value.list_for_options.return_value = []
        proc_cls.return_value.list_distinct_tag_values.return_value = []
        response = tm_client.get("/transformometro/gpt-actions/v1/catalog")
    assert response.status_code == 200
    return response.json()["data"]


def test_gpt_get_catalog_exposes_diagram_catalog(tm_client):
    data = _catalog_via_http(tm_client)
    assert "diagram_catalog" in data
    catalog = data["diagram_catalog"]
    assert catalog["format_version"] == 1
    assert isinstance(catalog["node_types"], list)
    assert len(catalog["node_types"]) == len(NODE_TYPES)
    assert "edge_kinds" in catalog
    assert "mermaid_conventions" in catalog


def test_diagram_catalog_source_is_canonical_builder_not_literals(tm_client):
    """Payload must equal build_bpmn_catalog_for_api() — no GPT-local copy."""
    data = _catalog_via_http(tm_client)
    assert data["diagram_catalog"] == build_bpmn_catalog_for_api()


def test_decision_supported_regression_for_teo(tm_client):
    """Exact failure: TÉO must see decision as supported from catalog evidence."""
    data = _catalog_via_http(tm_client)
    ids = {item["id"] for item in data["diagram_catalog"]["node_types"]}
    assert "decision" in ids
    assert "decision" in NODE_TYPES


def test_representative_gateways_and_tasks_exposed(tm_client):
    data = _catalog_via_http(tm_client)
    ids = {item["id"] for item in data["diagram_catalog"]["node_types"]}
    for node_type in (
        "decision",
        "gateway_parallel",
        "gateway_inclusive",
        "gateway_complex",
        "gateway_event",
        "task_user",
        "task_service",
        "task_manual",
        "task_script",
        "task_business_rule",
        "task_send",
        "task_receive",
        "subprocess",
        "call_activity",
        "start",
        "process",
        "end",
    ):
        assert node_type in NODE_TYPES, f"canonical missing {node_type}"
        assert node_type in ids, f"TÉO catalog missing {node_type}"


def test_every_exposed_node_type_accepted_by_validate_flowchart_v1(tm_client):
    data = _catalog_via_http(tm_client)
    for item in data["diagram_catalog"]["node_types"]:
        node_type = item["id"]
        doc = {
            "format": "flowchart_v1",
            "format_version": 1,
            "nodes": [
                {
                    "id": "n1",
                    "type": node_type,
                    "label": item.get("label") or node_type,
                    "position": {"x": 0, "y": 0},
                }
            ],
            "edges": [],
        }
        validate_flowchart_v1(doc)


def test_every_canonical_node_type_exposed_to_teo(tm_client):
    data = _catalog_via_http(tm_client)
    exposed = {item["id"] for item in data["diagram_catalog"]["node_types"]}
    assert exposed == set(NODE_TYPES)


def test_exposed_edge_kinds_match_canonical(tm_client):
    data = _catalog_via_http(tm_client)
    exposed = {item["id"] for item in data["diagram_catalog"]["edge_kinds"]}
    assert exposed == set(EDGE_KINDS)


def test_no_unsupported_node_type_exposed(tm_client):
    data = _catalog_via_http(tm_client)
    for item in data["diagram_catalog"]["node_types"]:
        assert item["id"] in NODE_TYPES


def test_node_type_entries_carry_minimum_fields(tm_client):
    data = _catalog_via_http(tm_client)
    for item in data["diagram_catalog"]["node_types"]:
        assert "id" in item
        assert "label" in item
        assert "category" in item
        assert "shape" in item
        assert "participates_in_flow" in item


def test_mermaid_remains_derived_in_catalog(tm_client):
    data = _catalog_via_http(tm_client)
    conventions = data["diagram_catalog"]["mermaid_conventions"]
    assert conventions["header"] == "flowchart TD"
    assert ":::bpmn_" in conventions["type_class_suffix"]
    assert "flowchart_v1" in conventions["source_of_truth"]
    assert "derivad" in conventions["source_of_truth"].lower() or "derived" in conventions[
        "source_of_truth"
    ].lower() or "vista" in conventions["source_of_truth"].lower()


def test_process_diagram_schema_still_requires_processo_id_and_conteudo():
    guide = build_registration_guide()
    schema = guide["entity_schemas"]["process_diagram"]
    assert schema["required"] == ["processo_id", "conteudo"]
    notes = " ".join(schema["notes"])
    assert "diagram_catalog" in notes
    assert "start/process/end" in notes


def test_registration_guide_does_not_duplicate_node_type_literals():
    """Guide must point to diagram_catalog, not embed NODE_TYPES list."""
    guide = build_registration_guide()
    blob = str(guide)
    for node_type in ("gateway_parallel", "task_user", "gateway_inclusive"):
        assert node_type not in blob
    notes = " ".join(guide["entity_schemas"]["process_diagram"]["notes"])
    assert "diagram_catalog" in notes


def test_action_count_unchanged_no_new_diagram_action():
    doc = build_gpt_actions_openapi()
    assert count_operations(doc) == 20
    assert len(GPT_ACTIONS_OPERATION_IDS) == 20
    assert "gpt_get_diagram_catalog" not in GPT_ACTIONS_OPERATION_IDS
    assert "gpt_get_catalog" in GPT_ACTIONS_OPERATION_IDS


def test_specialist_instructions_require_diagram_catalog_discovery():
    text = Path("docs/gpt-actions/specialist-instructions.md").read_text(encoding="utf-8")
    assert "diagram_catalog" in text
    assert "decision" in text
    assert "start/process/end" in text
