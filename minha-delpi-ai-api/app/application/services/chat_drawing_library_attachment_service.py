"""Registra PDF da biblioteca corporativa como anexo da sessão para exibição no chat."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any
from uuid import UUID

from werkzeug.utils import secure_filename

from app.domain.ports.chat_attachment_repository_port import ChatAttachmentRepositoryPort
from app.infrastructure.config.settings import Settings


class ChatDrawingLibraryAttachmentService:
    @classmethod
    def attachments_are_library_only(cls, attachments: list | None) -> bool:
        if not attachments:
            return False

        for item in attachments:
            if not isinstance(item, dict):
                return False

            meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}

            if meta.get("source") != "api_delpi_library":
                return False

        return True

    @classmethod
    def merge_into_turn_attachments(
        cls,
        attachments: list[dict] | None,
        *,
        user_id: UUID,
        session_id: UUID,
        tool_context: dict | None,
        attachment_repository: ChatAttachmentRepositoryPort | None,
        session,
    ) -> list[dict]:
        if attachments:
            return list(attachments)

        if not attachment_repository or session is None:
            return []

        if getattr(session, "user_id", None) != user_id:
            return []

        if not isinstance(tool_context, dict) or not tool_context.get("drawingAnalysisMode"):
            return []

        library_fetch = tool_context.get("drawingLibraryFetch")

        if not isinstance(library_fetch, dict):
            return []

        registered = cls._register_library_pdf(
            library_fetch=library_fetch,
            tool_context=tool_context,
            user_id=user_id,
            session_id=session_id,
            session=session,
            attachment_repository=attachment_repository,
        )

        if not registered:
            return []

        return [registered]

    @classmethod
    def _register_library_pdf(
        cls,
        *,
        library_fetch: dict[str, Any],
        tool_context: dict[str, Any],
        user_id: UUID,
        session_id: UUID,
        session,
        attachment_repository: ChatAttachmentRepositoryPort,
    ) -> dict[str, Any] | None:
        product_code = str(library_fetch.get("productCode") or "").strip().upper()
        storage_path = Path(str(library_fetch.get("storagePath") or "").strip())
        original_filename = (
            str(library_fetch.get("filename") or "").strip()
            or (f"{product_code}.pdf" if product_code else "desenho.pdf")
        )

        if not product_code or not storage_path.is_file():
            return None

        existing = cls._find_existing_library_attachment(
            attachment_repository=attachment_repository,
            user_id=user_id,
            session_id=session_id,
            product_code=product_code,
        )

        if existing:
            return cls._attachment_to_turn_dict(existing)

        content = storage_path.read_bytes()

        if not content.startswith(b"%PDF"):
            return None

        safe_name = secure_filename(original_filename) or "desenho.pdf"
        extension = Path(safe_name).suffix.lower() or ".pdf"
        storage_root = cls._storage_root()
        storage_dir = storage_root / str(user_id) / str(session_id)
        storage_dir.mkdir(parents=True, exist_ok=True)
        target_path = storage_dir / f"{uuid.uuid4().hex}{extension}"
        target_path.write_bytes(content)

        metadata = cls._build_attachment_metadata(
            library_fetch=library_fetch,
            tool_context=tool_context,
            product_code=product_code,
            original_filename=original_filename,
            extension=extension,
        )

        attachment = attachment_repository.create_attachment(
            user_id=user_id,
            session_id=session_id,
            project_id=session.project_id,
            agent_id=session.agent_id,
            filename=target_path.name,
            original_filename=original_filename,
            content_type="application/pdf",
            size_bytes=len(content),
            storage_path=str(target_path),
            metadata=metadata,
        )

        indexed_attachment = attachment_repository.update_status(
            attachment_id=attachment.id,
            status="indexed",
            metadata=metadata,
        )

        if indexed_attachment:
            attachment = indexed_attachment

        return cls._attachment_to_turn_dict(attachment)

    @classmethod
    def _find_existing_library_attachment(
        cls,
        *,
        attachment_repository: ChatAttachmentRepositoryPort,
        user_id: UUID,
        session_id: UUID,
        product_code: str,
    ):
        for attachment in attachment_repository.list_session_attachments(
            user_id=user_id,
            session_id=session_id,
        ):
            meta = attachment.metadata if isinstance(attachment.metadata, dict) else {}

            if (
                meta.get("source") == "api_delpi_library"
                and str(meta.get("productCode") or "").strip().upper() == product_code
                and Path(str(attachment.storage_path or "")).is_file()
            ):
                return attachment

        return None

    @classmethod
    def _build_attachment_metadata(
        cls,
        *,
        library_fetch: dict[str, Any],
        tool_context: dict[str, Any],
        product_code: str,
        original_filename: str,
        extension: str,
    ) -> dict[str, Any]:
        summary = tool_context.get("drawingPdfExtractSummary")
        document_vision = None
        char_count = None
        legible = None

        if isinstance(summary, dict):
            char_count = summary.get("charCount")
            legible = summary.get("legible")
            summary_vision = summary.get("documentVision")

            if isinstance(summary_vision, dict) and summary_vision:
                document_vision = dict(summary_vision)

        if not document_vision:
            tool_vision = tool_context.get("documentVision")

            if isinstance(tool_vision, dict) and tool_vision:
                document_vision = dict(tool_vision)

        preview: dict[str, Any] = {
            "kind": "document",
            "extension": extension,
            "extractor": "drawing_library",
        }

        if isinstance(char_count, int) and char_count > 0:
            preview["charCount"] = char_count

        metadata: dict[str, Any] = {
            "extension": extension,
            "storage": "local",
            "indexed": True,
            "source": "api_delpi_library",
            "productCode": product_code,
            "librarySource": library_fetch.get("source"),
            "preview": preview,
        }

        if isinstance(library_fetch.get("metadata"), dict):
            metadata["libraryMetadata"] = library_fetch["metadata"]

        if document_vision:
            metadata["documentVision"] = document_vision

            if legible is not None and document_vision.get("legible") is None:
                metadata["documentVision"]["legible"] = legible

        return metadata

    @classmethod
    def _attachment_to_turn_dict(cls, attachment) -> dict[str, Any]:
        return {
            "id": str(attachment.id),
            "filename": attachment.filename,
            "original_filename": attachment.original_filename,
            "content_type": attachment.content_type,
            "size_bytes": attachment.size_bytes,
            "status": attachment.status or "indexed",
            "metadata": attachment.metadata if isinstance(attachment.metadata, dict) else {},
        }

    @classmethod
    def _storage_root(cls) -> Path:
        root = Path(
            os.getenv("CHAT_ATTACHMENT_STORAGE_PATH")
            or getattr(Settings, "CHAT_ATTACHMENT_STORAGE_PATH", None)
            or "/tmp/minha-delpi-chat-attachments"
        )
        root.mkdir(parents=True, exist_ok=True)
        return root
