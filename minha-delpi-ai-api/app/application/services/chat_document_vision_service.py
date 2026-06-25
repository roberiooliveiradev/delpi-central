"""Visão e OCR de documentos no chat base — Onda 13."""

from __future__ import annotations

from typing import Any

from app.application.services.chat_document_vision.chat_document_vision_attachment_service import (
    ChatDocumentVisionAttachmentService,
)
from app.application.services.chat_document_vision.chat_document_vision_config_service import (
    ChatDocumentVisionConfigService,
)
from app.application.services.chat_document_vision.chat_document_vision_drawing_merge_service import (
    ChatDocumentVisionDrawingMergeService,
)
from app.application.services.chat_document_vision.chat_document_vision_pipeline_service import (
    ChatDocumentVisionPipelineService,
)
from app.application.services.chat_document_vision.chat_document_vision_stage_service import (
    ChatDocumentVisionStageService,
)
from app.application.services.chat_document_vision.document_vision_runtime import (
    _load_default_attachment_repository,
    _load_vision_runtime,
)

# Compatibilidade com patches de teste/scripts legados.
_vision_runtime = _load_vision_runtime
_default_attachment_repository = _load_default_attachment_repository

__all__ = ["ChatDocumentVisionService", "_default_attachment_repository", "_vision_runtime"]


class ChatDocumentVisionService:
    """Fachada — delegates em chat_document_vision/*."""

    SCHEMA_VERSION = ChatDocumentVisionAttachmentService.SCHEMA_VERSION

    @classmethod
    def is_enabled(cls) -> bool:
        return ChatDocumentVisionConfigService.is_enabled()

    @classmethod
    def should_run_for_attachment(
        cls,
        skills: dict | None,
        *,
        intent_route: str | None = None,
        has_agent: bool = False,
        message: str | None = None,
    ) -> bool:
        return ChatDocumentVisionAttachmentService.should_run_for_attachment(
            skills,
            intent_route=intent_route,
            has_agent=has_agent,
            message=message,
        )

    @classmethod
    def should_run_for_drawing(cls, skills: dict | None) -> bool:
        return ChatDocumentVisionAttachmentService.should_run_for_drawing(skills)

    @classmethod
    def enrich_drawing_extract(
        cls,
        parsed: dict[str, Any],
        *,
        user_id: str | None = None,
        session_id: str | None = None,
        attachment_ids: list | None = None,
        skills: dict | None = None,
        message: str | None = None,
    ) -> dict[str, Any]:
        return ChatDocumentVisionAttachmentService.enrich_drawing_extract(
            parsed,
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
            skills=skills,
        )

    @classmethod
    def to_document_vision_metadata(cls, vision: dict[str, Any]) -> dict[str, Any]:
        return ChatDocumentVisionAttachmentService.to_document_vision_metadata(vision)

    @classmethod
    def persist_attachment_vision_metadata(cls, attachment, vision_meta: dict[str, Any]) -> None:
        return ChatDocumentVisionAttachmentService.persist_attachment_vision_metadata(
            attachment,
            vision_meta,
        )

    @classmethod
    def refresh_attachment_vision_snapshot(
        cls,
        attachment,
        *,
        skills: dict | None = None,
        persist: bool = True,
    ) -> dict[str, Any] | None:
        return ChatDocumentVisionAttachmentService.refresh_attachment_vision_snapshot(
            attachment,
            skills=skills,
            persist=persist,
        )

    @classmethod
    def build_attachment_vision_metadata(
        cls,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
        attachment_ids: list | None = None,
        skills: dict | None = None,
        persist: bool = True,
        message: str | None = None,
        intent_route: str | None = None,
        has_agent: bool = False,
    ) -> dict[str, Any] | None:
        return ChatDocumentVisionAttachmentService.build_attachment_vision_metadata(
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
    def enrich_attachment_excerpt(
        cls,
        *,
        storage_path: str,
        filename: str,
        content_type: str | None,
        extracted_content: str,
        skills: dict | None = None,
        message: str | None = None,
    ) -> str:
        return ChatDocumentVisionAttachmentService.enrich_attachment_excerpt(
            storage_path=storage_path,
            filename=filename,
            content_type=content_type,
            extracted_content=extracted_content,
            skills=skills,
            message=message,
        )

    @classmethod
    def extract_from_storage_path(
        cls,
        storage_path: str,
        *,
        filename: str = "",
        content_type: str = "application/pdf",
        message: str | None = None,
        vision_purpose: str | None = None,
    ) -> dict[str, Any]:
        return ChatDocumentVisionPipelineService.extract_from_storage_path(
            storage_path,
            filename=filename,
            content_type=content_type,
            message=message,
            vision_purpose=vision_purpose,
        )

    @classmethod
    def merge_into_drawing_parse(
        cls,
        parsed: dict[str, Any] | None,
        vision: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return ChatDocumentVisionDrawingMergeService.merge_into_drawing_parse(parsed, vision)

    # --- Delegates privados (testes/scripts) ---

    @classmethod
    def _auto_vlm_fallback_enabled(cls) -> bool:
        return ChatDocumentVisionConfigService.auto_vlm_fallback_enabled()

    @classmethod
    def _image_describe_enabled(cls) -> bool:
        return ChatDocumentVisionConfigService.image_describe_enabled()

    @classmethod
    def _resolve_vision_purpose(
        cls,
        message: str | None,
        *,
        content_type: str = "",
        filename: str = "",
    ) -> str:
        return ChatDocumentVisionPipelineService.resolve_vision_purpose(
            message,
            content_type=content_type,
            filename=filename,
        )

    @classmethod
    def _needs_vlm_fallback(cls, text: str, *, legible: bool | None = None) -> bool:
        return ChatDocumentVisionPipelineService.needs_vlm_fallback(text, legible=legible)

    @classmethod
    def _maybe_vlm_fallback(cls, *args, **kwargs):
        return ChatDocumentVisionStageService.maybe_vlm_fallback(*args, **kwargs)

    @classmethod
    def _compute_vision_for_attachment(cls, *args, **kwargs):
        return ChatDocumentVisionAttachmentService.compute_vision_for_attachment(*args, **kwargs)

    @classmethod
    def _extract_drawing_pdf(cls, *args, **kwargs):
        return ChatDocumentVisionPipelineService.extract_drawing_pdf(*args, **kwargs)

    @classmethod
    def _extract_image_document(cls, *args, **kwargs):
        return ChatDocumentVisionStageService.extract_image_document(*args, **kwargs)

    @classmethod
    def _build_from_text(cls, *args, **kwargs):
        return ChatDocumentVisionPipelineService.build_from_text(*args, **kwargs)

    @classmethod
    def _finalize_result(cls, *args, **kwargs):
        return ChatDocumentVisionPipelineService.finalize_result(*args, **kwargs)

    @classmethod
    def _stage_native(cls, *args, **kwargs):
        return ChatDocumentVisionStageService.stage_native(*args, **kwargs)

    @classmethod
    def _stage_tesseract_pdf(cls, *args, **kwargs):
        return ChatDocumentVisionStageService.stage_tesseract_pdf(*args, **kwargs)

    @classmethod
    def _stage_tesseract_image(cls, *args, **kwargs):
        return ChatDocumentVisionStageService.stage_tesseract_image(*args, **kwargs)

    @classmethod
    def _stage_ollama_vlm(cls, *args, **kwargs):
        return ChatDocumentVisionStageService.stage_ollama_vlm(*args, **kwargs)

    @classmethod
    def _stage_neural_backend(cls, *args, **kwargs):
        return ChatDocumentVisionStageService.stage_neural_backend(*args, **kwargs)

    @classmethod
    def _stage_docling(cls, *args, **kwargs):
        return ChatDocumentVisionStageService.stage_docling(*args, **kwargs)

    @classmethod
    def _stage_paddleocr(cls, *args, **kwargs):
        return ChatDocumentVisionStageService.stage_paddleocr(*args, **kwargs)

    @classmethod
    def _maybe_enrich_with_description(cls, *args, **kwargs):
        return ChatDocumentVisionStageService.maybe_enrich_with_description(*args, **kwargs)

    @classmethod
    def _pil_to_base64_png(cls, *args, **kwargs):
        return ChatDocumentVisionStageService.pil_to_base64_png(*args, **kwargs)

    @classmethod
    def _parse_hybrid_vlm_response(cls, *args, **kwargs):
        return ChatDocumentVisionStageService.parse_hybrid_vlm_response(*args, **kwargs)

    @classmethod
    def _rasterize_pdf_pages(cls, *args, **kwargs):
        return ChatDocumentVisionStageService.rasterize_pdf_pages(*args, **kwargs)

    @classmethod
    def _truncate_vision_text(cls, text: str) -> str:
        return ChatDocumentVisionStageService.truncate_vision_text(text)

    @classmethod
    def _resolve_first_document_attachment(cls, *args, **kwargs):
        return ChatDocumentVisionAttachmentService.resolve_first_document_attachment(*args, **kwargs)

    @classmethod
    def _list_attachments(cls, *args, **kwargs):
        return ChatDocumentVisionAttachmentService.list_attachments(*args, **kwargs)

    @classmethod
    def _is_pdf(cls, content_type: str, filename: str, storage_path: str) -> bool:
        return ChatDocumentVisionConfigService.is_pdf(content_type, filename, storage_path)

    @classmethod
    def _is_image(cls, content_type: str, filename: str) -> bool:
        return ChatDocumentVisionConfigService.is_image(content_type, filename)

    @classmethod
    def _default_content_type(cls, filename: str) -> str:
        return ChatDocumentVisionConfigService.default_content_type(filename)
