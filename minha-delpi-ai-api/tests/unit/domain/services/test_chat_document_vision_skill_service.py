"""Ativação da skill document-vision-delpi — ChatDocumentVisionSkillService."""

from app.domain.services.chat_document_vision_skill_service import (
    ChatDocumentVisionSkillService,
)
from app.infrastructure.config.settings import Settings


def _enable_platform(monkeypatch) -> None:
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_ENABLED", "true")
    Settings.CHAT_DOCUMENT_VISION_ENABLED = True


def test_drawing_vision_requires_skill_or_auto_with_drawing(monkeypatch):
    _enable_platform(monkeypatch)
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING", "true")
    Settings.CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING = True

    assert ChatDocumentVisionSkillService.should_run_for_drawing(
        {"drawingAnalysis": True}
    )
    assert not ChatDocumentVisionSkillService.should_run_for_drawing(
        {"drawingAnalysis": False}
    )
    assert ChatDocumentVisionSkillService.should_run_for_drawing(
        {"documentVision": True, "drawingAnalysis": False}
    )


def test_attachment_turn_requires_skill_on_agent(monkeypatch):
    _enable_platform(monkeypatch)

    assert ChatDocumentVisionSkillService.should_run_for_attachment_turn(
        {"documentVision": True},
        intent_route="attachment_document",
        has_agent=True,
    )
    assert ChatDocumentVisionSkillService.should_run_for_attachment_turn(
        {"documentVision": False},
        intent_route="attachment_document",
        has_agent=True,
        message="descreva a imagem anexada",
    )
    assert not ChatDocumentVisionSkillService.should_run_for_attachment_turn(
        {"documentVision": False},
        intent_route="attachment_document",
        has_agent=True,
    )
    assert ChatDocumentVisionSkillService.should_run_for_attachment_turn(
        None,
        intent_route="attachment_document",
        has_agent=False,
    )


def test_attachment_turn_without_intent_requires_skill(monkeypatch):
    _enable_platform(monkeypatch)

    assert ChatDocumentVisionSkillService.should_run_for_attachment_turn(
        {"documentVision": True},
        has_agent=True,
    )
    assert not ChatDocumentVisionSkillService.should_run_for_attachment_turn(
        {"documentVision": False},
        has_agent=True,
    )


def test_resolve_drawing_activation_reports_reason(monkeypatch):
    _enable_platform(monkeypatch)
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING", "true")
    Settings.CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING = True

    activation = ChatDocumentVisionSkillService.resolve_drawing_activation(
        {"drawingAnalysis": True}
    )

    assert activation.enabled is True
    assert activation.mode == "drawing_enrich"
    assert activation.reason == "drawing_auto_vision"


def test_resolve_vision_purpose_describe_image():
    purpose = ChatDocumentVisionSkillService.resolve_vision_purpose(
        "descreva a imagem anexada",
        content_type="image/png",
        filename="foto.png",
    )

    assert purpose == "describe"


def test_resolve_vision_purpose_hybrid_when_read_and_describe():
    purpose = ChatDocumentVisionSkillService.resolve_vision_purpose(
        "descreva o pdf anexo e leia o pdf anexo",
        content_type="application/pdf",
        filename="doc.pdf",
    )

    assert purpose == "hybrid"
