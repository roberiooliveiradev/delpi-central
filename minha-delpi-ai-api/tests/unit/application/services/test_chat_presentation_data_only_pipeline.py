"""Regressão — pipeline não gera markdown template em turnos narrativos LLM."""

import pytest

from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.chat_response_mode_service import ChatResponseModeService
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


@pytest.fixture(autouse=True)
def enable_response_modes(monkeypatch):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)


def _use_case() -> ExecuteExternalActionUseCase:
    return ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )


def test_factory_status_pipeline_skips_template_markdown():
    envelope = load_api_delpi_fixture_with_meta("product_factory_status_90269002.json")
    path = "/products/90269002/factory-status"

    metadata = _use_case()._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope,
        resolved_path=path,
        request_parameters={
            "userMessage": "como esta o status fabril do produto 90269002?",
        },
    )

    assert metadata.get("dataOnlyPresentation") is True
    markdown = str((metadata.get("textPresentation") or {}).get("markdown") or "").strip()
    assert markdown == ""
    assert metadata.get("proseDeliveryMode") == "llm"
    assert metadata.get("llmProseDecoupled") is True
    assert metadata.get("treePresentation") or metadata.get("tablePresentations")


def test_factual_stock_pipeline_keeps_template_markdown():
    envelope = load_api_delpi_fixture_with_meta("product_stock_90269001.json")
    path = "/products/90269001/stock"

    metadata = _use_case()._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope,
        resolved_path=path,
        request_parameters={
            "userMessage": "qual o saldo na filial 01 do produto 90269001?",
        },
    )

    assert not metadata.get("dataOnlyPresentation")
    markdown = str((metadata.get("textPresentation") or {}).get("markdown") or "").strip()
    assert markdown
