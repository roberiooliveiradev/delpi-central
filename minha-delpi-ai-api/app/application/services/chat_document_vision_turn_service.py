"""Orquestração de visão/OCR por turno — skill document-vision-delpi (application)."""

from __future__ import annotations

from typing import Any, Callable

from app.application.services.chat_document_vision_service import ChatDocumentVisionService
from app.application.services.chat_stream_activity_service import ChatStreamActivityService
from app.domain.services.chat_document_vision_skill_service import (
    ChatDocumentVisionSkillService,
    DocumentVisionActivation,
)


class ChatDocumentVisionTurnService:
    @classmethod
    def should_run_for_drawing(cls, skills: dict | None = None) -> bool:
        return ChatDocumentVisionSkillService.should_run_for_drawing(skills)

    @classmethod
    def should_run_for_attachment_turn(
        cls,
        skills: dict | None = None,
        *,
        intent_route: str | None = None,
        has_agent: bool = False,
    ) -> bool:
        return ChatDocumentVisionSkillService.should_run_for_attachment_turn(
            skills,
            intent_route=intent_route,
            has_agent=has_agent,
        )

    @classmethod
    def enrich_drawing_extract(
        cls,
        parsed: dict[str, Any] | None,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
        attachment_ids: list | None = None,
        skills: dict | None = None,
    ) -> dict[str, Any]:
        if not cls.should_run_for_drawing(skills):
            return dict(parsed) if isinstance(parsed, dict) else {}

        return ChatDocumentVisionService.enrich_drawing_extract(
            parsed,
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
            skills=skills,
        )

    @classmethod
    def build_attachment_vision_metadata(
        cls,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
        attachment_ids: list | None = None,
        skills: dict | None = None,
        intent_route: str | None = None,
        has_agent: bool = False,
        persist: bool = True,
        message: str | None = None,
    ) -> dict[str, Any] | None:
        activation = ChatDocumentVisionSkillService.resolve_attachment_turn_activation(
            skills,
            intent_route=intent_route,
            has_agent=has_agent,
        )

        if not activation.enabled:
            return None

        return ChatDocumentVisionService.build_attachment_vision_metadata(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
            skills=skills,
            persist=persist,
            message=message,
            intent_route=intent_route,
            has_agent=has_agent,
        )

    @classmethod
    def run_drawing_vision_with_progress(
        cls,
        *,
        parsed: dict[str, Any] | None,
        user_id: str | None = None,
        session_id: str | None = None,
        attachment_ids: list | None = None,
        skills: dict | None = None,
        on_stream_activity: Callable[..., Any] | None = None,
    ) -> tuple[dict[str, Any], DocumentVisionActivation]:
        activation = ChatDocumentVisionSkillService.resolve_drawing_activation(skills)

        if activation.enabled and on_stream_activity:
            ChatStreamActivityService.emit_document_vision_progress(
                on_stream_activity,
                phase="start",
            )
            ChatStreamActivityService.emit_document_vision_progress(
                on_stream_activity,
                phase="ocr",
            )

        enriched = cls.enrich_drawing_extract(
            parsed,
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
            skills=skills,
        )

        if activation.enabled and on_stream_activity and enriched:
            engine = (
                enriched.get("extractor")
                or enriched.get("visionEngine")
                or "document_vision"
            )
            ChatStreamActivityService.emit_document_vision_progress(
                on_stream_activity,
                phase="complete",
                engine=str(engine),
                char_count=int(enriched.get("charCount") or 0),
            )

        return enriched, activation

    @classmethod
    def run_attachment_vision_with_progress(
        cls,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
        attachment_ids: list | None = None,
        skills: dict | None = None,
        intent_route: str | None = None,
        has_agent: bool = False,
        on_stream_activity: Callable[..., Any] | None = None,
        persist: bool = True,
        message: str | None = None,
    ) -> tuple[dict[str, Any] | None, DocumentVisionActivation]:
        activation = ChatDocumentVisionSkillService.resolve_attachment_turn_activation(
            skills,
            intent_route=intent_route,
            has_agent=has_agent,
        )

        if not activation.enabled:
            return None, activation

        if on_stream_activity:
            ChatStreamActivityService.emit_document_vision_progress(
                on_stream_activity,
                phase="start",
            )
            ChatStreamActivityService.emit_document_vision_progress(
                on_stream_activity,
                phase="ocr",
            )

        metadata = cls.build_attachment_vision_metadata(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
            skills=skills,
            intent_route=intent_route,
            has_agent=has_agent,
            persist=persist,
            message=message,
        )

        if on_stream_activity and metadata:
            ChatStreamActivityService.emit_document_vision_progress(
                on_stream_activity,
                phase="complete",
                engine=str(metadata.get("engine") or "document_vision"),
                char_count=int(metadata.get("charCount") or 0),
            )

        return metadata, activation
