"""Executa OCR/visão de documentos em processo filho (spawn).

Segfaults em Pillow/fitz (_imaging) matam só o filho — o Flask/SSE do pai segue vivo.
Espelha o espírito do isolamento antiword em workspace extraction.
"""

from __future__ import annotations

import logging
import multiprocessing as mp
import os
import pickle
import tempfile
import time
from typing import Any, Callable

from app.domain.exceptions.vision_exceptions import (
    VisionMemoryLimitedError,
    VisionOcrProcessCrashedError,
)

logger = logging.getLogger(__name__)

_JOB_ATTACHMENT_METADATA = "attachment_metadata"
_JOB_ENRICH_DRAWING = "enrich_drawing"
_JOB_EXTRACT_DRAWING_PDF = "extract_drawing_pdf"


def _dispatch_job(job: dict[str, Any]) -> Any:
    kind = str(job.get("kind") or "").strip()
    kwargs = dict(job.get("kwargs") or {})

    if kind == _JOB_ATTACHMENT_METADATA:
        from app.application.services.chat_document_vision_turn_service import (
            ChatDocumentVisionTurnService,
        )

        return ChatDocumentVisionTurnService.build_attachment_vision_metadata(**kwargs)

    if kind == _JOB_ENRICH_DRAWING:
        from app.application.services.chat_document_vision_service import (
            ChatDocumentVisionService,
        )

        parsed = kwargs.pop("parsed", None)
        return ChatDocumentVisionService.enrich_drawing_extract(parsed, **kwargs)

    if kind == _JOB_EXTRACT_DRAWING_PDF:
        from app.application.services.chat_document_vision_service import (
            ChatDocumentVisionService,
        )

        storage_path = str(kwargs.get("storage_path") or "")
        filename = str(kwargs.get("filename") or "")
        return ChatDocumentVisionService._extract_drawing_pdf(
            storage_path,
            filename=filename,
        )

    raise ValueError(f"unsupported_document_vision_ocr_job:{kind}")


def document_vision_ocr_child_main(job: dict[str, Any], result_path: str) -> None:
    """Entry point do processo filho (precisa ser top-level para spawn)."""
    exit_code = 1
    payload: dict[str, Any]

    try:
        from app.main import app

        with app.app_context():
            value = _dispatch_job(job)
        payload = {"ok": True, "value": value}
        exit_code = 0
    except BaseException as exc:
        payload = {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "code": getattr(exc, "code", None),
        }
        logger.exception(
            "document_vision_ocr_child_failed",
            extra={"job_kind": str((job or {}).get("kind") or "")},
        )

    try:
        with open(result_path, "wb") as handle:
            pickle.dump(payload, handle, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception:
        logger.exception("document_vision_ocr_child_write_failed")
        raise SystemExit(2) from None

    raise SystemExit(exit_code)


def _load_result(result_path: str) -> dict[str, Any] | None:
    try:
        with open(result_path, "rb") as handle:
            payload = pickle.load(handle)
    except (OSError, pickle.PickleError, EOFError):
        return None

    return payload if isinstance(payload, dict) else None


def _raise_from_child_payload(payload: dict[str, Any]) -> None:
    error_type = str(payload.get("error_type") or "")
    message = str(payload.get("error") or "document_vision_ocr_child_error")

    if error_type == "VisionMemoryLimitedError" or payload.get("code") == (
        VisionMemoryLimitedError.code
    ):
        raise VisionMemoryLimitedError(message)

    if error_type == "MemoryError":
        raise MemoryError(message)

    raise RuntimeError(f"{error_type}: {message}" if error_type else message)


class DocumentVisionOcrProcessRunner:
    JOB_ATTACHMENT_METADATA = _JOB_ATTACHMENT_METADATA
    JOB_ENRICH_DRAWING = _JOB_ENRICH_DRAWING
    JOB_EXTRACT_DRAWING_PDF = _JOB_EXTRACT_DRAWING_PDF

    @classmethod
    def run(
        cls,
        job: dict[str, Any],
        *,
        timeout_seconds: float,
        heartbeat: Callable[[], None] | None = None,
        heartbeat_interval_seconds: float = 20.0,
    ) -> Any:
        fd, result_path = tempfile.mkstemp(prefix="delpi-docvis-ocr-", suffix=".pkl")
        os.close(fd)

        ctx = mp.get_context("spawn")
        process = ctx.Process(
            target=document_vision_ocr_child_main,
            args=(job, result_path),
            daemon=True,
        )
        started = time.monotonic()

        try:
            process.start()
            interval = max(0.05, float(heartbeat_interval_seconds or 20.0))
            timeout = max(1.0, float(timeout_seconds or 300.0))

            while process.is_alive():
                elapsed = time.monotonic() - started
                if elapsed >= timeout:
                    process.terminate()
                    process.join(timeout=5)
                    if process.is_alive():
                        process.kill()
                        process.join(timeout=2)
                    raise VisionOcrProcessCrashedError(
                        "vision_ocr_process_timeout",
                        exit_code=process.exitcode,
                    )

                process.join(timeout=interval)
                if process.is_alive() and heartbeat is not None:
                    heartbeat()

            exit_code = process.exitcode
            payload = _load_result(result_path)

            if exit_code is not None and exit_code < 0:
                raise VisionOcrProcessCrashedError(
                    f"vision_ocr_process_signal_{-exit_code}",
                    exit_code=exit_code,
                )

            if payload is None:
                raise VisionOcrProcessCrashedError(
                    "vision_ocr_process_no_result",
                    exit_code=exit_code,
                )

            if payload.get("ok"):
                return payload.get("value")

            # Filho gravou erro lógico (ex.: MemoryError / VisionMemoryLimitedError).
            _raise_from_child_payload(payload)
        finally:
            try:
                os.unlink(result_path)
            except OSError:
                pass
