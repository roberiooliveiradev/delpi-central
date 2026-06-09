"""Ativação canônica da skill document-vision-delpi — reutilizável em desenho, anexos e imagens."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)
from app.domain.services.chat_domain_config_service import ChatDomainConfigService


@dataclass(frozen=True)
class DocumentVisionActivation:
    enabled: bool
    mode: str
    reason: str = ""


class ChatDocumentVisionSkillService:
    @classmethod
    def is_platform_enabled(cls) -> bool:
        return ChatDomainConfigService.chat_document_vision_enabled()

    @classmethod
    def is_skill_active(cls, skills: dict | None) -> bool:
        return bool((skills or {}).get("documentVision"))

    @classmethod
    def allows_attachment_document_turn(
        cls,
        *,
        runtime_skills: dict | None = None,
        has_agent: bool = False,
        message: str | None = None,
    ) -> bool:
        if not cls.is_platform_enabled():
            return False

        if cls.is_skill_active(runtime_skills):
            return True

        if not has_agent:
            return True

        if message:
            from app.domain.services.chat_attachment_document_intent_service import (
                ChatAttachmentDocumentIntentService,
            )

            if ChatAttachmentDocumentIntentService.is_document_content_question(message):
                return True

        return False

    @classmethod
    def should_run_for_drawing(cls, skills: dict | None = None) -> bool:
        if not cls.is_platform_enabled():
            return False

        resolved = skills if isinstance(skills, dict) else {}

        if resolved.get("documentVision"):
            return True

        return bool(
            ChatDomainConfigService.chat_document_vision_auto_with_drawing()
            and resolved.get("drawingAnalysis")
        )

    @classmethod
    def should_run_for_attachment_turn(
        cls,
        skills: dict | None = None,
        *,
        intent_route: str | None = None,
        has_agent: bool = False,
        message: str | None = None,
    ) -> bool:
        if not cls.is_platform_enabled():
            return False

        resolved = skills if isinstance(skills, dict) else {}

        if resolved.get("documentVision"):
            return True

        normalized_intent = str(intent_route or "").strip().lower()

        if normalized_intent == "attachment_document":
            return cls.allows_attachment_document_turn(
                runtime_skills=resolved,
                has_agent=has_agent,
                message=message,
            )

        if message and cls.allows_attachment_document_turn(
            runtime_skills=resolved,
            has_agent=has_agent,
            message=message,
        ):
            return True

        return False

    @classmethod
    def resolve_drawing_activation(cls, skills: dict | None = None) -> DocumentVisionActivation:
        if not cls.should_run_for_drawing(skills):
            return DocumentVisionActivation(
                enabled=False,
                mode=ChatDocumentVisionContentService.activation_mode("none"),
                reason=ChatDocumentVisionContentService.activation_reason("platformDisabled"),
            )

        resolved = skills if isinstance(skills, dict) else {}
        reason = (
            ChatDocumentVisionContentService.activation_reason("skillEnabled")
            if resolved.get("documentVision")
            else ChatDocumentVisionContentService.activation_reason("drawingAutoVision")
        )

        return DocumentVisionActivation(
            enabled=True,
            mode=ChatDocumentVisionContentService.activation_mode("drawingEnrich"),
            reason=reason,
        )

    @classmethod
    def resolve_attachment_turn_activation(
        cls,
        skills: dict | None = None,
        *,
        intent_route: str | None = None,
        has_agent: bool = False,
    ) -> DocumentVisionActivation:
        if not cls.should_run_for_attachment_turn(
            skills,
            intent_route=intent_route,
            has_agent=has_agent,
        ):
            return DocumentVisionActivation(
                enabled=False,
                mode=ChatDocumentVisionContentService.activation_mode("none"),
                reason=ChatDocumentVisionContentService.activation_reason("platformDisabled"),
            )

        resolved = skills if isinstance(skills, dict) else {}
        normalized_intent = str(intent_route or "").strip().lower()

        if resolved.get("documentVision"):
            reason = ChatDocumentVisionContentService.activation_reason("skillEnabled")
        elif normalized_intent == "attachment_document":
            reason = ChatDocumentVisionContentService.activation_reason(
                "attachmentDocumentIntent"
            )
        else:
            reason = ChatDocumentVisionContentService.activation_reason("chatCommonPlatform")

        return DocumentVisionActivation(
            enabled=True,
            mode=ChatDocumentVisionContentService.activation_mode("attachmentTurn"),
            reason=reason,
        )

    @classmethod
    def resolve_vision_purpose(
        cls,
        message: str | None,
        *,
        content_type: str = "",
        filename: str = "",
    ) -> str:
        from app.domain.services.chat_attachment_document_intent_service import (
            ChatAttachmentDocumentIntentService,
        )

        normalized = str(message or "").strip()
        is_image = cls._is_image_attachment(content_type, filename)
        wants_describe = ChatAttachmentDocumentIntentService.is_image_describe_question(
            normalized
        ) if normalized else False
        wants_ocr = (
            any(
                pattern.search(normalized)
                for pattern in ChatDocumentVisionContentService.read_content_patterns()
            )
            if normalized
            else False
        )

        hybrid = ChatDocumentVisionContentService.vision_purpose("hybrid")
        describe = ChatDocumentVisionContentService.vision_purpose("describe")
        ocr = ChatDocumentVisionContentService.vision_purpose("ocr")

        if wants_describe and wants_ocr:
            return hybrid

        if wants_describe:
            return describe if is_image else hybrid

        if wants_ocr or normalized:
            return ocr

        return ocr

    @classmethod
    def _is_image_attachment(cls, content_type: str, filename: str) -> bool:
        lowered_type = str(content_type or "").strip().lower()
        lowered_name = str(filename or "").strip().lower()

        if lowered_type.startswith("image/"):
            return True

        extensions = ChatDocumentVisionContentService.image_extensions()

        return any(lowered_name.endswith(ext) for ext in extensions)
