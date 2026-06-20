"""Testes — pipeline data-only (P2): sem prosa template quando LLM narrará."""

import pytest

from app.domain.services.chat_presentation_data_only_prose_service import (
    ChatPresentationDataOnlyProseService,
)
from app.domain.services.chat_response_mode_service import ChatResponseModeService


def test_should_apply_when_narrative_message_and_modes_enabled(monkeypatch):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)

    assert ChatPresentationDataOnlyProseService.should_apply(
        "como esta o status fabril do produto 90269001?",
        path="/products/90269001/factory-status",
    )


def test_should_not_apply_without_user_message(monkeypatch):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)

    assert not ChatPresentationDataOnlyProseService.should_apply(
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
