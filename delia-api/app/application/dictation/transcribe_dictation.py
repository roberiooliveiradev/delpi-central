"""TranscribeDictation — bounded dictation→text use case (VD-F03).

Enforcement order is deliberate and fail-closed: AuthZ (`delia.access`)
→ syntactic/semantic limits → rate limit → provider port → postcondition.
Raw audio is never logged, persisted, or placed in prompts/embeddings;
the returned text is untrusted user input, never authorization.
"""

from __future__ import annotations

import time
import uuid
from typing import Callable, Protocol

from app.application.dictation.contracts import (
    AUDIO_MIME_TO_FORMAT,
    DICTATION_CONTRACT_VERSION,
    SUPPORTED_LANGUAGE,
    DictationTranscriptionRequest,
    DictationTranscriptionResult,
    normalize_mime,
)
from app.application.dictation.errors import (
    DURATION_EXCEEDED,
    EMPTY_TRANSCRIPTION,
    FORBIDDEN,
    PAYLOAD_TOO_LARGE,
    PROVIDER_UNAVAILABLE,
    RATE_LIMITED,
    UNSUPPORTED_LANGUAGE,
    UNSUPPORTED_MEDIA,
    DictationError,
)
from app.application.interaction.handle_interactive_turn import (
    has_delia_access,
)
from app.application.ports.speech_transcription_port import (
    SpeechTranscriptionRequest,
)


class _Clock(Protocol):
    def __call__(self) -> float:  # monotonic seconds
        ...


class _PerUserWindowLimiter:
    """Bounded fixed-window per-user limiter (single-replica honest bound).

    Contract §3: honest in-process rate control; not cross-replica
    enforcement (documented residual). Memory is bounded by an explicit
    subject cap — oldest windows are evicted, never unbounded growth.
    """

    _MAX_SUBJECTS = 10_000

    def __init__(self, limit_per_minute: int, clock: _Clock) -> None:
        self._limit = max(1, int(limit_per_minute))
        self._clock = clock
        self._windows: dict[str, tuple[float, int]] = {}

    def allow(self, subject: str) -> bool:
        now = self._clock()
        start, count = self._windows.get(subject, (now, 0))
        if now - start >= 60.0:
            start, count = now, 0
        if count >= self._limit:
            self._windows[subject] = (start, count)
            return False
        if len(self._windows) >= self._MAX_SUBJECTS and subject not in (
            self._windows
        ):
            # Bounded eviction: drop the single oldest window.
            oldest = min(self._windows, key=lambda k: self._windows[k][0])
            self._windows.pop(oldest, None)
        self._windows[subject] = (start, count + 1)
        return True


class TranscribeDictation:
    """dictation.transcription.v1 use case."""

    def __init__(
        self,
        *,
        port,
        max_audio_bytes: int,
        max_duration_ms: int,
        rate_limit_per_minute: int,
        clock: _Clock = time.monotonic,
        transcription_id_factory: Callable[[], str] | None = None,
    ) -> None:
        if port is None:
            raise ValueError("TranscribeDictation requires a port")
        self._port = port
        self._max_audio_bytes = int(max_audio_bytes)
        self._max_duration_ms = int(max_duration_ms)
        self._limiter = _PerUserWindowLimiter(rate_limit_per_minute, clock)
        self._transcription_id_factory = transcription_id_factory or (
            lambda: str(uuid.uuid4())
        )

    def execute(
        self, request: DictationTranscriptionRequest
    ) -> DictationTranscriptionResult:
        if not has_delia_access(request.access_context):
            raise DictationError(
                FORBIDDEN, "delia.access is required for dictation"
            )

        mime = normalize_mime(request.mime_type)
        provider_format = AUDIO_MIME_TO_FORMAT.get(mime)
        if provider_format is None:
            raise DictationError(
                UNSUPPORTED_MEDIA, "audio mime type is not supported"
            )

        if (request.language_hint or "").strip() != SUPPORTED_LANGUAGE:
            raise DictationError(
                UNSUPPORTED_LANGUAGE,
                "only pt-BR dictation is supported by this contract",
            )

        if (
            not isinstance(request.duration_ms, int)
            or isinstance(request.duration_ms, bool)
            or request.duration_ms <= 0
            or request.duration_ms > self._max_duration_ms
        ):
            raise DictationError(
                DURATION_EXCEEDED, "audio duration exceeds contract limits"
            )

        if (
            not isinstance(request.audio_bytes, (bytes, bytearray))
            or len(request.audio_bytes) == 0
        ):
            raise DictationError(
                UNSUPPORTED_MEDIA, "audio payload is empty"
            )
        if len(request.audio_bytes) > self._max_audio_bytes:
            raise DictationError(
                PAYLOAD_TOO_LARGE, "audio payload exceeds contract limits"
            )

        subject = (request.access_context.user_id or "").strip() or "unknown"
        if not self._limiter.allow(subject):
            raise DictationError(
                RATE_LIMITED, "dictation rate limit exceeded"
            )

        try:
            text = self._port.transcribe(
                SpeechTranscriptionRequest(
                    audio_bytes=bytes(request.audio_bytes),
                    provider_format=provider_format,
                    language_hint=SUPPORTED_LANGUAGE,
                    timeout_hint_ms=None,
                )
            )
        except DictationError:
            raise
        # Raw provider/transport exceptions must not leak above the port,
        # but defence-in-depth keeps the boundary fail-closed.
        except Exception as exc:
            raise DictationError(
                PROVIDER_UNAVAILABLE, "transcription provider failed"
            ) from exc

        normalized = (text or "").strip()
        if not normalized:
            # Contract postcondition: a completed transcription must
            # contain text. Silence/unintelligible audio is a typed
            # failure, never fabricated content.
            raise DictationError(
                EMPTY_TRANSCRIPTION,
                "provider returned no transcription text",
            )

        return DictationTranscriptionResult(
            transcription_id=self._transcription_id_factory(),
            text=normalized,
            language=SUPPORTED_LANGUAGE,
        )


__all__ = [
    "DICTATION_CONTRACT_VERSION",
    "TranscribeDictation",
]
