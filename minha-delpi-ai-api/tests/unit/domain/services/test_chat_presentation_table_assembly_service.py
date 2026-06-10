"""Montagem declarativa de tablePresentations — Playbook 12 R3."""

from __future__ import annotations

from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.chat_presentation_table_assembly_service import (
    ChatPresentationTableAssemblyService,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def _use_case() -> ExecuteExternalActionUseCase:
    return ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )


def test_production_status_assembly_assigns_profile_and_primary_tables() -> None:
    envelope = load_api_delpi_fixture_with_meta("product_production_status_90269002.json")
    path = "/products/90269002/production-status"
    meta = _use_case()._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope,
        resolved_path=path,
        request_parameters={"userMessage": "status de produção do produto 90269002"},
    )

    tables = meta.get("tablePresentations") or []

    assert len(tables) >= 2
    assert meta.get("profileTablePresentation", {}).get("role") == "profile"
    assert any(table.get("role") == "list" for table in tables)


def test_analyser_assembly_assigns_profile_guide_and_inspection_slots() -> None:
    envelope = load_api_delpi_fixture_with_meta("product_analyser_90269001.json")
    path = "/products/90269001/analyser"
    meta = _use_case()._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope,
        resolved_path=path,
        request_parameters={"userMessage": "analise completa do produto 90269001"},
    )

    assert meta.get("profileTablePresentation", {}).get("type") == "table"
    assert len(meta.get("tablePresentations") or []) >= 1


def test_factory_status_assembly_builds_multiple_tables() -> None:
    envelope = load_api_delpi_fixture_with_meta("product_factory_status_90269002.json")
    path = "/products/90269002/factory-status"
    meta = _use_case()._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope,
        resolved_path=path,
        request_parameters={"userMessage": "status fabril do produto 90269002"},
    )

    tables = meta.get("tablePresentations") or []

    assert len(tables) >= 2
    assert meta.get("profileTablePresentation", {}).get("role") == "profile"


def test_stock_assembly_respects_requires_items() -> None:
    envelope = load_api_delpi_fixture_with_meta("product_stock_90269001.json")
    path = "/products/90269001/stock"
    meta = _use_case()._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope,
        resolved_path=path,
        request_parameters={"userMessage": "estoque do produto 90269001"},
    )

    tables = meta.get("tablePresentations") or []

    assert len(tables) >= 2
    assert meta.get("profileTablePresentation", {}).get("role") == "profile"


def test_tree_hierarchy_assembly_builds_structure_table() -> None:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

    presenter = ExternalActionResultPresenter()
    path = "/products/90269001/structure"
    payload = {
        "root": {
            "code": "90269001",
            "description": "ITEM",
            "type": "PA",
            "unit": "UN",
            "quantity": 1,
        },
        "items": [
            {
                "code": "C1",
                "description": "COMP",
                "type": "PI",
                "unit": "UN",
                "quantity": 1.0,
                "components": [
                    {
                        "code": "C2",
                        "description": "SUB",
                        "type": "MP",
                        "unit": "UN",
                        "quantity": 2.0,
                    }
                ],
            }
        ],
        "total": 1,
    }

    result = ChatPresentationTableAssemblyService.assemble(
        presenter,
        payload,
        path,
        session_format="table",
    )

    assert len(result.table_presentations) == 1
    assert result.table_presentation is not None
    assert result.table_presentation.get("type") == "table"
    assert result.table_presentation.get("rows")
