"""Dictation HTTP boundary — dictation.transcription.v1 (VD-F03).

GET  /dictation/status          — capability admission + contract limits
POST /dictation/transcriptions  — bounded audio → untrusted editable text

AuthN is enforced by the registered auth middleware; AuthZ
(`delia.access`) is enforced inside the use case against the
Core-resolved PlatformAccessContext. This module performs syntactic
validation only. Raw audio and transcript text are never logged —
only bounded metadata (mime, bytes, duration, codes, request_id).
"""

from __future__ import annotations

import base64
import binascii
import logging
import math

from flask import (
    Blueprint,
    Flask,
    current_app,
    g,
    jsonify,
    request,
)

from app.application.dictation.contracts import (
    DICTATION_CONTRACT_VERSION,
    SUPPORTED_LANGUAGE,
    DictationTranscriptionRequest,
)
from app.application.interaction.handle_interactive_turn import (
    has_delia_access,
)
from app.application.dictation.errors import (
    DURATION_EXCEEDED,
    EMPTY_TRANSCRIPTION,
    FORBIDDEN,
    INTERNAL_ERROR,
    INVALID_REQUEST,
    PAYLOAD_TOO_LARGE,
    PROVIDER_REJECTED,
    PROVIDER_TIMEOUT,
    PROVIDER_UNAVAILABLE,
    RATE_LIMITED,
    TRANSCRIPTION_UNAVAILABLE,
    UNSUPPORTED_LANGUAGE,
    UNSUPPORTED_MEDIA,
    DictationError,
)

ALLOWED_BODY_KEYS = frozenset(
    {"audio_base64", "mime_type", "duration_ms", "language_hint"}
)

_ERROR_STATUS = {
    "unauthenticated": 401,
    FORBIDDEN: 403,
    INVALID_REQUEST: 400,
    UNSUPPORTED_LANGUAGE: 400,
    DURATION_EXCEEDED: 400,
    UNSUPPORTED_MEDIA: 415,
    PAYLOAD_TOO_LARGE: 413,
    RATE_LIMITED: 429,
    TRANSCRIPTION_UNAVAILABLE: 503,
    PROVIDER_UNAVAILABLE: 503,
    PROVIDER_REJECTED: 502,
    EMPTY_TRANSCRIPTION: 502,
    PROVIDER_TIMEOUT: 504,
    INTERNAL_ERROR: 500,
}


def register_dictation_routes(app: Flask, logger: logging.Logger) -> None:
    bp = Blueprint("dictation", __name__)

    @bp.get("/dictation/status")
    def get_dictation_status():
        # Same Core-resolved AuthZ boundary as the transcription use
        # case: an authenticated user without `delia.access` must not
        # learn the capability surface (VD-F03 hardening).
        if not has_delia_access(getattr(g, "platform_access", None)):
            logger.info(
                "dictation_status_rejected reason=forbidden request_id=%s",
                getattr(g, "request_id", None),
            )
            return _error(
                FORBIDDEN, "delia.access is required for dictation"
            )
        limits = current_app.config.get("DICTATION_LIMITS") or {}
        handler = current_app.config.get("DICTATION_TRANSCRIPTION_HANDLER")
        return jsonify(
            {
                "contract_version": DICTATION_CONTRACT_VERSION,
                "available": handler is not None,
                "language": SUPPORTED_LANGUAGE,
                "max_audio_bytes": limits.get("max_audio_bytes"),
                "max_duration_ms": limits.get("max_duration_ms"),
            }
        ), 200

    @bp.post("/dictation/transcriptions")
    def submit_dictation_transcription():
        request_id = getattr(g, "request_id", None)
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            logger.info(
                "dictation_rejected reason=malformed_body request_id=%s",
                request_id,
            )
            return _error(INVALID_REQUEST, "request body must be a JSON object")

        extra_keys = set(body) - ALLOWED_BODY_KEYS
        if extra_keys:
            logger.info(
                "dictation_rejected reason=unknown_keys request_id=%s",
                request_id,
            )
            return _error(INVALID_REQUEST, "unknown request fields")

        handler = current_app.config.get("DICTATION_TRANSCRIPTION_HANDLER")
        if handler is None:
            logger.info(
                "dictation_rejected reason=not_configured request_id=%s",
                request_id,
            )
            return _error(
                TRANSCRIPTION_UNAVAILABLE,
                "dictation transcription is not configured",
            )

        limits = current_app.config.get("DICTATION_LIMITS") or {}
        max_audio_bytes = int(limits.get("max_audio_bytes") or 0)

        audio_b64 = body.get("audio_base64")
        mime_type = body.get("mime_type")
        duration_ms = body.get("duration_ms")
        language_hint = body.get("language_hint", SUPPORTED_LANGUAGE)

        if not isinstance(audio_b64, str) or not audio_b64:
            return _error(INVALID_REQUEST, "audio_base64 is required")
        if not isinstance(mime_type, str) or not mime_type.strip():
            return _error(INVALID_REQUEST, "mime_type is required")
        if not isinstance(duration_ms, int) or isinstance(duration_ms, bool):
            return _error(INVALID_REQUEST, "duration_ms must be an integer")

        # Reject oversized payloads BEFORE decoding: the encoded form is
        # ~4/3 of the raw audio, so the bound can be checked on length.
        if max_audio_bytes > 0 and len(audio_b64) > (
            4 * math.ceil(max_audio_bytes / 3) + 8
        ):
            logger.info(
                "dictation_rejected reason=payload_too_large request_id=%s",
                request_id,
            )
            return _error(
                PAYLOAD_TOO_LARGE, "audio payload exceeds contract limits"
            )
        try:
            audio_bytes = base64.b64decode(audio_b64, validate=True)
        except (binascii.Error, ValueError):
            return _error(INVALID_REQUEST, "audio_base64 is not valid base64")
        if max_audio_bytes > 0 and len(audio_bytes) > max_audio_bytes:
            logger.info(
                "dictation_rejected reason=payload_too_large request_id=%s",
                request_id,
            )
            return _error(
                PAYLOAD_TOO_LARGE, "audio payload exceeds contract limits"
            )

        try:
            result = handler.execute(
                DictationTranscriptionRequest(
                    access_context=getattr(g, "platform_access", None),
                    audio_bytes=audio_bytes,
                    mime_type=mime_type,
                    duration_ms=duration_ms,
                    language_hint=(
                        language_hint
                        if isinstance(language_hint, str)
                        else ""
                    ),
                )
            )
        except DictationError as exc:
            logger.info(
                "dictation_failed code=%s mime=%s bytes=%s duration_ms=%s "
                "request_id=%s",
                exc.code,
                mime_type,
                len(audio_bytes),
                duration_ms,
                request_id,
            )
            return _error(exc.code, exc.message)
        except Exception as exc:
            # Privacy: no traceback/message — an unexpected exception
            # could carry provider payload, transcript text, or request
            # material in str(exc). Type name + request_id keep the
            # failure diagnosable without leaking content.
            logger.error(
                "dictation_failed code=internal_error exc_type=%s "
                "request_id=%s",
                type(exc).__name__,
                request_id,
            )
            return _error(INTERNAL_ERROR, "internal error")

        # Metadata only — transcript text and audio are never logged.
        logger.info(
            "dictation_transcribed transcription_id=%s mime=%s bytes=%s "
            "duration_ms=%s request_id=%s",
            result.transcription_id,
            mime_type,
            len(audio_bytes),
            duration_ms,
            request_id,
        )
        return jsonify(
            {
                "transcription_id": result.transcription_id,
                "text": result.text,
                "language": result.language,
            }
        ), 200

    app.register_blueprint(bp)


def _error(code: str, message: str):
    status = _ERROR_STATUS.get(code, 500)
    return jsonify({"detail": message, "code": code}), status
