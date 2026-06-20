"""Testes — pipeline data-only (P2): sem prosa template quando LLM narrará."""

from unittest.mock import MagicMock

import pytest

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_data_only_prose_service import (
    ChatPresentationDataOnlyProseService,
)
from app.domain.services.chat_response_mode_service import ChatResponseModeService

configure_domain_infrastructure_ports()


def test_should_apply_when_narrative_message_and_modes_enabled(monkeypatch):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)

    assert ChatPresentationDataOnlyProseService.should_apply(
        "como esta o status fabril do produto 90269001?",
        path="/products/90269001/factory-status",
    )


def test_should_not_apply_without_user_message_when_not_everywhere(monkeypatch):
    from app.domain.services.chat_presentation_prose_delivery_content_service import (
        ChatPresentationProseDeliveryContentService,
    )

    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)
    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "llm_prose_everywhere",
        lambda: False,
    )
    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "deprecate_humanized_linhas_as_prose",
        lambda: False,
    )

    assert not ChatPresentationDataOnlyProseService.should_apply(
        None,
        path="/products/90269001/factory-status",
    )


def test_should_apply_with_path_only_when_llm_everywhere(monkeypatch):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)

    assert ChatPresentationDataOnlyProseService.should_apply(
        None,
        path="/products/90269001/factory-status",
    )


def test_prepare_humanized_strips_linhas_and_archives():
    metadata = {"dataOnlyPresentation": True}
    humanized = {
        "titulo": "Status fabril",
        "linhas": ["- OP 12 em andamento."],
        "linhas_detalhe": ["- Filial 01: 10 un."],
    }

    prepared = ChatPresentationDataOnlyProseService.prepare_humanized_for_metadata(
        metadata,
        humanized,
    )

    assert prepared == {"titulo": "Status fabril"}
    archive = metadata["templateProseArchive"]["humanizedSummary"]
    assert archive["linhas"] == ["- OP 12 em andamento."]
    assert archive["linhas_detalhe"] == ["- Filial 01: 10 un."]


def test_resolve_title_only_uses_profile_spec(monkeypatch):
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

    presenter = ExternalActionResultPresenter()
    metadata = {
        "dataOnlyPresentation": True,
        "dataAnswer": {"profileKey": "factory_status"},
    }

    titulo = ChatPresentationDataOnlyProseService._resolve_title_only(
        presenter,
        {"data": {"product": {"code": "90269002"}}},
        path="/products/90269002/factory-status",
        metadata=metadata,
    )

    assert "90269002" in titulo
    assert "fábrica" in titulo.lower()


def test_resolve_humanized_summary_skips_present():
    presenter = MagicMock()
    presenter.present.side_effect = AssertionError("present() não deve ser chamado")

    metadata = {"dataOnlyPresentation": True, "dataAnswer": {"profileKey": "stock"}}
    presenter._unwrap_data.return_value = {"product": {"code": "90269001"}}
    presenter._extract_product_code_from_path.return_value = "90269001"
    presenter._route_presentation.side_effect = lambda *args, **kwargs: "unused"
    presenter._presenter_content.return_value._path_fragment_title.return_value = None
    presenter._fallback_title.return_value = None
    presenter._presenter_text.return_value = "fallback"

    result = ChatPresentationDataOnlyProseService.resolve_humanized_summary(
        presenter,
        {"data": {"product": {"code": "90269001"}}},
        path="/products/90269001/stock",
        metadata=metadata,
    )

    presenter.present.assert_not_called()
    assert result == {"titulo": "Estoque do produto 90269001"}


def test_resolve_humanized_summary_sql_preserves_rows_without_linhas():
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

    presenter = ExternalActionResultPresenter()
    metadata = {"dataOnlyPresentation": True}
    payload = {
        "success": True,
        "data": {
            "rows": [{"COD_PRODUTO": "90264130", "QTD_PLANEJADA": 1200}],
            "total": 1,
        },
    }

    result = ChatPresentationDataOnlyProseService.resolve_humanized_summary(
        presenter,
        payload,
        path="/data/sql",
        metadata=metadata,
    )

    assert isinstance(result, dict)
    assert result.get("sqlRows")
    assert not result.get("linhas")
    assert metadata.get("templateProseArchive", {}).get("humanizedSummary", {}).get("linhas")


def test_finalize_metadata_clears_text_and_rebuilds_render_plan():
    metadata = {
        "dataOnlyPresentation": True,
        "textPresentation": {"markdown": "### Status\n\nTemplate longo."},
        "humanizedSummary": {"titulo": "Status", "linhas": ["- Item"]},
        "presentationDecision": {"layoutMode": "stack"},
        "stackPresentationPlan": {
            "narrativeOrder": ["lead", "tailVisuals"],
            "tailVisualOrder": ["tree"],
        },
        "treePresentation": {
            "type": "tree",
            "title": "Estrutura",
            "root": {"id": "1", "label": "90269001", "children": []},
        },
    }

    ChatPresentationDataOnlyProseService.finalize_metadata(metadata)

    assert metadata["textPresentation"]["markdown"] == ""
    assert metadata["humanizedSummary"]["linhas"] == []
    assert metadata["proseDeliveryMode"] == "llm"
    lead = next(
        segment
        for segment in metadata["renderPlan"]["segments"]
        if segment.get("slot") == "lead"
    )
    assert lead["source"] == "assistantMessage"
