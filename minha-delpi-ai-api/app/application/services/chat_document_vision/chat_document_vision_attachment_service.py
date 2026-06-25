"""Anexos e metadata — visão de documentos."""

from __future__ import annotations

import base64
import os
import time
from io import BytesIO
from pathlib import Path
from typing import Any
from uuid import UUID

from app.infrastructure.config.settings import Settings

from app.application.services.chat_document_vision.chat_document_vision_config_service import (
    ChatDocumentVisionConfigService,
)
from app.application.services.chat_document_vision.chat_document_vision_drawing_merge_service import (
    ChatDocumentVisionDrawingMergeService,
)
from app.application.services.chat_document_vision.chat_document_vision_facade_access import vision_service
from app.application.services.chat_document_vision.document_vision_runtime import (
    default_attachment_repository,
)


class ChatDocumentVisionAttachmentService:
    SCHEMA_VERSION = "1.0"

    @classmethod
    def should_run_for_attachment(
        cls,
        skills: dict | None = None,
        *,
        intent_route: str | None = None,
        has_agent: bool = False,
        message: str | None = None,
    ) -> bool:
        from app.domain.services.chat_document_vision_skill_service import (
            ChatDocumentVisionSkillService,
        )

        return ChatDocumentVisionSkillService.should_run_for_attachment_turn(
            skills,
            intent_route=intent_route,
            has_agent=has_agent,
            message=message,
        )

    @classmethod
    def should_run_for_drawing(cls, skills: dict | None) -> bool:
        from app.domain.services.chat_document_vision_skill_service import (
            ChatDocumentVisionSkillService,
        )

        return ChatDocumentVisionSkillService.should_run_for_drawing(skills)

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
        base = dict(parsed) if isinstance(parsed, dict) else {}

        if not cls.should_run_for_drawing(skills):
            return base

        attachment = vision_service()._resolve_first_document_attachment(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
        )

        if not attachment:
            return base

        vision = vision_service()._extract_drawing_pdf(
            attachment.storage_path,
            filename=attachment.original_filename or "",
        )

        merged = ChatDocumentVisionDrawingMergeService.merge_into_drawing_parse(base, vision)

        if vision:
            vision_service().persist_attachment_vision_metadata(
                attachment,
                vision_service().to_document_vision_metadata(vision),
            )

        return merged

    @classmethod
    def to_document_vision_metadata(cls, vision: dict[str, Any]) -> dict[str, Any]:
        bom_rows = vision.get("bomRows") if isinstance(vision.get("bomRows"), list) else []

        title_block = vision.get("titleBlock")
        text_excerpt = vision_service()._truncate_vision_text(str(vision.get("fullText") or ""))
        image_description = vision_service()._truncate_vision_text(
            str(vision.get("imageDescription") or "")
        )

        return {
            "schemaVersion": vision.get("schemaVersion") or cls.SCHEMA_VERSION,
            "engine": vision.get("engine"),
            "stages": vision.get("stages") or [],
            "legibilityScore": vision.get("legibilityScore"),
            "durationMs": vision.get("durationMs"),
            "charCount": vision.get("charCount"),
            "legible": vision.get("legible"),
            "pageCount": vision.get("pageCount"),
            "pagesProcessed": vision.get("pagesProcessed") or vision.get("pageCount"),
            "bomRowCount": len(bom_rows),
            "hasTitleBlock": bool(title_block),
            "tableCount": len(vision.get("tables") or [])
            if isinstance(vision.get("tables"), list)
            else 0,
            "visionPurpose": vision.get("visionPurpose"),
            "textExcerpt": text_excerpt or None,
            "imageDescription": image_description or None,
            "hasImageDescription": bool(image_description),
            "filename": vision.get("filename"),
        }

    @classmethod
    def compute_vision_for_attachment(
        cls,
        attachment,
        *,
        skills: dict | None = None,
        message: str | None = None,
        intent_route: str | None = None,
        has_agent: bool = False,
    ) -> dict[str, Any] | None:
        if not cls.should_run_for_attachment(
            skills,
            intent_route=intent_route,
            has_agent=has_agent,
            message=message,
        ):
            return None

        filename = attachment.original_filename or ""
        content_type = attachment.content_type or ChatDocumentVisionConfigService.default_content_type(filename)

        if not ChatDocumentVisionConfigService.is_vision_target(content_type, filename, attachment.storage_path):
            return None

        if str(attachment.status or "").lower() == "indexed":
            from app.domain.services.chat_document_vision_content_service import (
                ChatDocumentVisionContentService,
            )

            purpose = vision_service()._resolve_vision_purpose(
                message,
                content_type=content_type,
                filename=filename,
            )
            describe_purpose = ChatDocumentVisionContentService.vision_purpose("describe")
            hybrid_purpose = ChatDocumentVisionContentService.vision_purpose("hybrid")

            native = vision_service()._stage_native(
                attachment.storage_path,
                filename=filename,
                content_type=content_type,
            )
            text = str(native.get("fullText") or "").strip()
            min_legible = max(1, int(Settings.CHAT_DOCUMENT_VISION_MIN_LEGIBLE_CHARS))
            source_metadata = (
                native.get("metadata") if isinstance(native.get("metadata"), dict) else {}
            )
            extractor = str(source_metadata.get("extractor") or native.get("engine") or "")
            is_image = ChatDocumentVisionConfigService.is_image(content_type, filename)
            metadata_only_image = is_image and extractor == "image_metadata"
            needs_semantic_vision = purpose in {describe_purpose, hybrid_purpose}

            if (
                len(text) < min_legible
                or metadata_only_image
                or needs_semantic_vision
            ):
                return vision_service().extract_from_storage_path(
                    attachment.storage_path,
                    filename=filename,
                    content_type=content_type,
                    message=message,
                )

            started = time.perf_counter()
            built = vision_service()._build_from_text(
                text,
                engine=str(native.get("engine") or "native"),
                stages=["native"],
                source_metadata=native.get("metadata") if isinstance(native.get("metadata"), dict) else {},
            )

            result = vision_service()._finalize_result(
                built,
                engine=str(built.get("engine") or "native"),
                stages=["native"],
                warnings=[],
                started=started,
                vision_purpose=vision_service()._resolve_vision_purpose(
                    message,
                    content_type=content_type,
                    filename=filename,
                ),
            )
            result["filename"] = filename
            return vision_service()._maybe_enrich_with_description(
                result,
                storage_path=attachment.storage_path,
                filename=filename,
                content_type=content_type,
                message=message,
            )

        vision = vision_service().extract_from_storage_path(
            attachment.storage_path,
            filename=filename,
            content_type=content_type,
            message=message,
        )
        vision["filename"] = filename
        return vision

    @classmethod
    def persist_attachment_vision_metadata(
        cls,
        attachment,
        vision_meta: dict[str, Any],
    ) -> None:
        if not attachment or not vision_meta:
            return

        try:
            attachment_id = UUID(str(attachment.id))
        except (TypeError, ValueError):
            return

        try:
            from datetime import datetime, timezone

            default_attachment_repository().update_status(
                attachment_id=attachment_id,
                status=str(attachment.status or "ready"),
                metadata={
                    "documentVision": vision_meta,
                    "documentVisionAt": datetime.now(timezone.utc).isoformat(),
                },
            )
        except Exception:
            return

    @classmethod
    def refresh_attachment_vision_snapshot(
        cls,
        attachment,
        *,
        skills: dict | None = None,
        persist: bool = True,
    ) -> dict[str, Any] | None:
        """Recalcula visão/OCR e opcionalmente grava em `attachment.metadata.documentVision`."""
        vision = cls.compute_vision_for_attachment(attachment, skills=skills)

        if not vision:
            return None

        meta = cls.to_document_vision_metadata(vision)

        if persist:
            cls.persist_attachment_vision_metadata(attachment, meta)

        return meta

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
        """Snapshot leve para metadata/adminDebug em turnos só com anexo (ex.: boleto PDF)."""
        attachment = vision_service()._resolve_first_document_attachment(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
        )

        if not attachment:
            return None

        vision = cls.compute_vision_for_attachment(
            attachment,
            skills=skills,
            message=message,
            intent_route=intent_route,
            has_agent=has_agent,
        )

        if not vision:
            return None

        meta = cls.to_document_vision_metadata(vision)

        if persist:
            cls.persist_attachment_vision_metadata(attachment, meta)

        return meta

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
        if not vision_service().should_run_for_attachment(skills):
            return extracted_content

        if not ChatDocumentVisionConfigService.is_vision_target(content_type, filename, storage_path):
            return extracted_content

        resolved_type = content_type or ChatDocumentVisionConfigService.default_content_type(filename)
        vision = vision_service().extract_from_storage_path(
            storage_path,
            filename=filename,
            content_type=resolved_type,
            message=message,
        )
        ocr_text = str(vision.get("fullText") or "").strip()
        image_description = str(vision.get("imageDescription") or "").strip()
        blocks: list[str] = []

        if image_description:
            from app.domain.services.chat_document_vision_content_service import (
                ChatDocumentVisionContentService,
            )

            blocks.append(
                "\n".join(
                    [
                        ChatDocumentVisionContentService.context_label("descriptionLabel"),
                        image_description,
                    ]
                )
            )

        if ocr_text:
            blocks.append(ocr_text)

        if not blocks:
            return extracted_content

        vision_excerpt = "\n\n".join(blocks).strip()

        if ChatDocumentVisionConfigService.should_replace_attachment_content(extracted_content, vision_excerpt):
            return vision_excerpt

        if not extracted_content.strip():
            return vision_excerpt

        return f"{extracted_content.strip()}\n\n{vision_excerpt}".strip()

    @classmethod
    def resolve_first_document_attachment(
        cls,
        *,
        user_id: str | None,
        session_id: str | None,
        attachment_ids: list | None,
    ):
        attachments = vision_service()._list_attachments(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
        )

        if not attachments:
            return None

        pdf_match = None
        image_match = None

        for attachment in attachments:
            name = str(attachment.original_filename or "").lower()
            content_type = str(attachment.content_type or "").lower()

            if content_type == "application/pdf" or name.endswith(".pdf"):
                return attachment

            if image_match is None and ChatDocumentVisionConfigService.is_image(content_type, name):
                image_match = attachment

        return image_match

    @classmethod
    def list_attachments(
        cls,
        *,
        user_id: str | None,
        session_id: str | None,
        attachment_ids: list | None,
    ):
        if not user_id or not session_id or not attachment_ids:
            return []

        try:
            repository = default_attachment_repository()
            ids = []

            for raw in attachment_ids:
                try:
                    ids.append(UUID(str(raw)))
                except (TypeError, ValueError):
                    continue

            if not ids:
                return []

            return repository.list_attachments_by_ids(
                user_id=UUID(str(user_id)),
                session_id=UUID(str(session_id)),
                attachment_ids=ids,
            )
        except Exception:
            return []
