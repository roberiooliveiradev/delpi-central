"""Regressão do pipeline de apresentação — schema-first (Playbook 22)."""

from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def _use_case() -> ExecuteExternalActionUseCase:
    return ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )


def test_factory_status_schema_first_metadata():
    envelope = load_api_delpi_fixture_with_meta("product_factory_status_90269002.json")
    path = "/products/90269002/factory-status"

    meta = _use_case()._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope,
        resolved_path=path,
        request_parameters={"userMessage": "status fabril"},
    )

    assert meta.get("presentationDecision")
    assert meta.get("tablePresentation") or meta.get("textPresentation")


def test_structure_exclusivity_schema_first_metadata():
    envelope = load_api_delpi_fixture_with_meta("product_structure_exclusivity_90261805.json")
    path = "/products/90261805/structure/exclusivity"

    meta = _use_case()._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope,
        resolved_path=path,
        request_parameters={"userMessage": "exclusividade"},
    )

    assert meta.get("presentationDecision")
    assert meta.get("tablePresentation") or meta.get("textPresentation")


def test_stock_schema_first_metadata():
    envelope = load_api_delpi_fixture_with_meta("product_stock_90269001.json")
    path = "/products/90269001/stock"

    meta = _use_case()._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope,
        resolved_path=path,
        request_parameters={"userMessage": "estoque"},
    )

    assert meta.get("presentationDecision")
    assert meta.get("tablePresentation") or meta.get("textPresentation")
