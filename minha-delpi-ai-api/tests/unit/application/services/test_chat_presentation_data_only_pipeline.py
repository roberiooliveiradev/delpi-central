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


@pytest.fixture(autouse=True)
def stub_column_label_llm(monkeypatch):
    from app.domain.services.presentation_column_label_llm_service import (
        PresentationColumnLabelLlmService,
    )

    monkeypatch.setattr(PresentationColumnLabelLlmService, "generate", lambda *a, **k: "")


def _assert_data_only_contract(metadata: dict) -> None:
    assert metadata.get("dataOnlyPresentation") is True
    markdown = str((metadata.get("textPresentation") or {}).get("markdown") or "").strip()
    assert markdown == ""
    assert metadata.get("proseDeliveryMode") == "llm"


def _has_table_evidence(metadata: dict) -> bool:
    for key in ("tablePresentation", "presentation"):
        presentation = metadata.get(key) or {}

        if presentation.get("type") == "table" and presentation.get("rows"):
            return True

    bulk = metadata.get("tablePresentations")

    if isinstance(bulk, list) and bulk:
        return True

    return "table" in (metadata.get("availableFormats") or [])


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
            "userMessage": "qual o status do produto 90269002 na fabrica hoje?",
        },
    )

    _assert_data_only_contract(metadata)
    assert metadata.get("llmProseDecoupled") is True
    assert metadata.get("dataAnswer") or metadata.get("renderPlan")


def test_factory_status_pipeline_data_only_when_modes_disabled_require_false(monkeypatch):
    from app.domain.services.chat_presentation_prose_delivery_content_service import (
        ChatPresentationProseDeliveryContentService,
    )

    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: False)
    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "require_response_modes_for_llm_prose",
        lambda: False,
    )

    envelope = load_api_delpi_fixture_with_meta("product_factory_status_90269002.json")
    path = "/products/90269002/factory-status"

    metadata = _use_case()._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope,
        resolved_path=path,
        request_parameters={
            "userMessage": "qual o status do produto 90269002 na fabrica hoje?",
        },
    )

    assert metadata.get("dataOnlyPresentation") is True
    assert str((metadata.get("textPresentation") or {}).get("markdown") or "").strip() == ""


def test_factual_stock_pipeline_skips_template_when_llm_everywhere():
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

    _assert_data_only_contract(metadata)


def test_playbook_top_items_pipeline_data_only():
    envelope = load_api_delpi_fixture_with_meta("production_consumption_top_items.json")
    path = "/production/consumption/top-items"

    metadata = _use_case()._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope,
        resolved_path=path,
        request_parameters={
            "userMessage": "Quais itens mais consumidos no mês passado top 10?",
        },
    )

    _assert_data_only_contract(metadata)
    assert metadata.get("llmProseDecoupled") is True
    assert _has_table_evidence(metadata)


def test_kpi_cpv_pipeline_data_only():
    envelope = load_api_delpi_fixture_with_meta("supplies_cpv.json")
    path = "/supplies/cpv"

    metadata = _use_case()._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope,
        resolved_path=path,
        request_parameters={
            "userMessage": "Qual o CPV da empresa?",
        },
    )

    _assert_data_only_contract(metadata)
    presentation = metadata.get("presentation") or {}
    assert presentation.get("type") == "kpi" or metadata.get("kpiPresentation")


def test_sql_pipeline_data_only():
    envelope = load_api_delpi_fixture_with_meta("data_sql_rows.json")
    path = "/data/sql"

    metadata = _use_case()._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope,
        resolved_path=path,
        request_parameters={
            "userMessage": "Liste os produtos com OP planejada esta semana",
        },
    )

    _assert_data_only_contract(metadata)
    assert _has_table_evidence(metadata)
