"""Orquestração de visão/OCR por turno — skill document-vision-delpi (application)."""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable, TypeVar

from app.application.services.chat_document_vision_service import ChatDocumentVisionService
from app.application.services.chat_stream_activity_service import ChatStreamActivityService
from app.domain.exceptions.vision_exceptions import (
    VisionMemoryLimitedError,
    VisionOcrProcessCrashedError,
)
from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)
from app.domain.services.chat_document_vision_skill_service import (
    ChatDocumentVisionSkillService,
    DocumentVisionActivation,
)
from app.domain.services.chat_vision_memory_guard_service import (
    ChatVisionMemoryGuardService,
)
from app.infrastructure.vision.document_vision_ocr_process_runner import (
    DocumentVisionOcrProcessRunner,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ChatDocumentVisionTurnService:
    @staticmethod
    def _capture_flask_app():
        try:
            from flask import current_app, has_app_context

            if has_app_context():
                return current_app._get_current_object()
        except RuntimeError:
            return None

        return None

    @classmethod
    def _attach_process_crashed_metadata(
        cls,
        payload: dict[str, Any] | None,
        *,
        exit_code: int | None = None,
    ) -> dict[str, Any]:
        merged = dict(payload) if isinstance(payload, dict) else {}
        merged["processCrashed"] = True
        merged["engine"] = merged.get("engine") or "none"
        merged["charCount"] = int(merged.get("charCount") or 0)
        if exit_code is not None:
            merged["processExitCode"] = int(exit_code)
        return merged

    @classmethod
    def _run_blocking_with_ocr_heartbeat(
        cls,
        operation: Callable[[], T],
        *,
        on_stream_activity: Callable[..., Any] | None,
    ) -> T:
        if on_stream_activity is None:
            return operation()

        flask_app = cls._capture_flask_app()
        result: dict[str, T] = {}
        error: list[BaseException] = []
        done = threading.Event()

        def worker() -> None:
            try:
                if flask_app is not None:
                    with flask_app.app_context():
                        result["value"] = operation()
                else:
                    result["value"] = operation()
            except BaseException as exc:
                error.append(exc)
            finally:
                done.set()

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

        interval = ChatStreamActivityService.ocr_heartbeat_interval_seconds()

        while not done.wait(timeout=interval):
            on_stream_activity(ChatStreamActivityService.document_vision_ocr_heartbeat())

        if error:
            raise error[0]

        return result["value"]

    @classmethod
    def _run_ocr_job(
        cls,
        job: dict[str, Any],
        *,
        inline_operation: Callable[[], T],
        on_stream_activity: Callable[..., Any] | None,
    ) -> T:
        if not ChatDocumentVisionContentService.process_isolation_enabled():
            return cls._run_blocking_with_ocr_heartbeat(
                inline_operation,
                on_stream_activity=on_stream_activity,
            )

        def _heartbeat() -> None:
            if on_stream_activity is None:
                return
            on_stream_activity(ChatStreamActivityService.document_vision_ocr_heartbeat())

        return DocumentVisionOcrProcessRunner.run(
            job,
            timeout_seconds=float(
                ChatDocumentVisionContentService.process_isolation_timeout_seconds()
            ),
            heartbeat=_heartbeat if on_stream_activity is not None else None,
            heartbeat_interval_seconds=ChatStreamActivityService.ocr_heartbeat_interval_seconds(),
        )

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
        on_stream_activity: Callable[..., Any] | None = None,
    ) -> dict[str, Any]:
        if not cls.should_run_for_drawing(skills):
            return dict(parsed) if isinstance(parsed, dict) else {}

        kwargs = {
            "parsed": parsed,
            "user_id": user_id,
            "session_id": session_id,
            "attachment_ids": attachment_ids,
            "skills": skills,
        }

        return cls._run_ocr_job(
            {
                "kind": DocumentVisionOcrProcessRunner.JOB_ENRICH_DRAWING,
                "kwargs": kwargs,
            },
            inline_operation=lambda: ChatDocumentVisionService.enrich_drawing_extract(
                parsed,
                user_id=user_id,
                session_id=session_id,
                attachment_ids=attachment_ids,
                skills=skills,
            ),
            on_stream_activity=on_stream_activity,
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

        try:
            enriched = cls.enrich_drawing_extract(
                parsed,
                user_id=user_id,
                session_id=session_id,
                attachment_ids=attachment_ids,
                skills=skills,
                on_stream_activity=on_stream_activity,
            )
        except (MemoryError, VisionMemoryLimitedError):
            ChatVisionMemoryGuardService.release_ocr_memory()
            enriched = ChatVisionMemoryGuardService.attach_memory_limited_metadata(
                dict(parsed) if isinstance(parsed, dict) else {}
            )
        except VisionOcrProcessCrashedError as exc:
            logger.error(
                "document_vision_ocr_process_crashed",
                extra={"exit_code": exc.exit_code, "mode": "drawing_enrich"},
            )
            ChatVisionMemoryGuardService.release_ocr_memory()
            enriched = cls._attach_process_crashed_metadata(
                dict(parsed) if isinstance(parsed, dict) else {},
                exit_code=exc.exit_code,
            )

        enriched = cls._apply_llm_solve_for_attachments(
            enriched,
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
            on_stream_activity=on_stream_activity,
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
    def run_drawing_vision_from_storage_path(
        cls,
        *,
        parsed: dict[str, Any] | None,
        storage_path: str,
        filename: str,
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

        base = dict(parsed) if isinstance(parsed, dict) else {}

        if not cls.should_run_for_drawing(skills):
            return base, activation

        try:
            vision = cls._run_ocr_job(
                {
                    "kind": DocumentVisionOcrProcessRunner.JOB_EXTRACT_DRAWING_PDF,
                    "kwargs": {
                        "storage_path": storage_path,
                        "filename": filename,
                    },
                },
                inline_operation=lambda: ChatDocumentVisionService._extract_drawing_pdf(
                    storage_path,
                    filename=filename,
                ),
                on_stream_activity=on_stream_activity,
            )
            enriched = ChatDocumentVisionService.merge_into_drawing_parse(base, vision)
        except (MemoryError, VisionMemoryLimitedError):
            ChatVisionMemoryGuardService.release_ocr_memory()
            enriched = ChatVisionMemoryGuardService.attach_memory_limited_metadata(base)
            # Ainda tenta VLM no pai — OCR pode ter falhado por memória.
            enriched = cls._apply_llm_solve_in_parent(
                storage_path,
                filename=filename,
                pdf_extract=enriched,
                on_stream_activity=on_stream_activity,
            )
            return enriched, activation
        except VisionOcrProcessCrashedError as exc:
            logger.error(
                "document_vision_ocr_process_crashed",
                extra={"exit_code": exc.exit_code, "mode": "drawing_storage"},
            )
            ChatVisionMemoryGuardService.release_ocr_memory()
            enriched = cls._attach_process_crashed_metadata(base, exit_code=exc.exit_code)
            enriched = cls._apply_llm_solve_in_parent(
                storage_path,
                filename=filename,
                pdf_extract=enriched,
                on_stream_activity=on_stream_activity,
            )
            return enriched, activation

        enriched = cls._apply_llm_solve_in_parent(
            storage_path,
            filename=filename,
            pdf_extract=enriched,
            on_stream_activity=on_stream_activity,
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
    def _apply_llm_solve_in_parent(
        cls,
        storage_path: str,
        *,
        filename: str,
        pdf_extract: dict[str, Any] | None,
        on_stream_activity: Callable[..., Any] | None = None,
    ) -> dict[str, Any]:
        """VLM/LLM no processo Flask — fora do filho OCR (segfault Pillow)."""
        from app.application.services.chat_drawing_extraction_llm_solve_service import (
            ChatDrawingExtractionLlmSolveService,
        )

        payload = dict(pdf_extract) if isinstance(pdf_extract, dict) else {}

        if on_stream_activity:
            ChatStreamActivityService.emit_document_vision_progress(
                on_stream_activity,
                phase="vlm",
            )

        return ChatDrawingExtractionLlmSolveService.apply_if_needed(
            storage_path,
            filename=filename or "",
            pdf_extract=payload,
        )

    @classmethod
    def _apply_llm_solve_for_attachments(
        cls,
        pdf_extract: dict[str, Any] | None,
        *,
        user_id: str | None,
        session_id: str | None,
        attachment_ids: list | None,
        on_stream_activity: Callable[..., Any] | None = None,
    ) -> dict[str, Any]:
        payload = dict(pdf_extract) if isinstance(pdf_extract, dict) else {}
        attachment = ChatDocumentVisionService._resolve_first_document_attachment(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
        )

        if not attachment:
            return payload

        return cls._apply_llm_solve_in_parent(
            str(attachment.storage_path or ""),
            filename=str(attachment.original_filename or ""),
            pdf_extract=payload,
            on_stream_activity=on_stream_activity,
        )

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

        kwargs = {
            "user_id": user_id,
            "session_id": session_id,
            "attachment_ids": attachment_ids,
            "skills": skills,
            "intent_route": intent_route,
            "has_agent": has_agent,
            "persist": persist,
            "message": message,
        }

        try:
            metadata = cls._run_ocr_job(
                {
                    "kind": DocumentVisionOcrProcessRunner.JOB_ATTACHMENT_METADATA,
                    "kwargs": kwargs,
                },
                inline_operation=lambda: cls.build_attachment_vision_metadata(**kwargs),
                on_stream_activity=on_stream_activity,
            )
        except (MemoryError, VisionMemoryLimitedError):
            ChatVisionMemoryGuardService.release_ocr_memory()
            metadata = ChatVisionMemoryGuardService.attach_memory_limited_metadata(
                {"engine": "none", "charCount": 0}
            )
        except VisionOcrProcessCrashedError as exc:
            logger.error(
                "document_vision_ocr_process_crashed",
                extra={"exit_code": exc.exit_code, "mode": "attachment"},
            )
            ChatVisionMemoryGuardService.release_ocr_memory()
            metadata = cls._attach_process_crashed_metadata(
                {"engine": "none", "charCount": 0},
                exit_code=exc.exit_code,
            )

        if on_stream_activity and metadata:
            ChatStreamActivityService.emit_document_vision_progress(
                on_stream_activity,
                phase="complete",
                engine=str(metadata.get("engine") or "document_vision"),
                char_count=int(metadata.get("charCount") or 0),
            )

        return metadata, activation
