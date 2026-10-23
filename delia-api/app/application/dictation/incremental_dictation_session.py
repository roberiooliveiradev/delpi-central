"""IncrementalDictationService — dictation.incremental.v1 (VD-F06).

A session binds ordered audio segments captured while the user is still
speaking. Each segment is a COMPLETE audio blob admitted synchronously
(AuthZ → session validity/ownership → sequence → semantic bounds →
in-flight bound) and then transcribed for real by the provider port —
``stream_transcribe`` yields cumulative snapshots that become `partial`
events, and the last snapshot closes the segment exactly once as
`final`. Provider failures surface as typed `error` events mid-stream;
admission failures raise DictationError before any byte is emitted.

Sessions live only in this process (same honest bound as the v1
per-user rate limiter — documented residual). Raw audio, transcript
text and secrets are never logged or persisted.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from typing import Callable, Iterator

from app.application.dictation.contracts import (
    AUDIO_MIME_TO_FORMAT,
    EVENT_ERROR,
    EVENT_FINAL,
    EVENT_PARTIAL,
    EVENT_STARTED,
    INCREMENTAL_CONTRACT_NAME,
    INCREMENTAL_CONTRACT_VERSION,
    SUPPORTED_LANGUAGE,
    IncrementalDictationSession,
    normalize_mime,
)
from app.application.dictation.errors import (
    DURATION_EXCEEDED,
    FORBIDDEN,
    INVALID_SEQUENCE,
    PAYLOAD_TOO_LARGE,
    PROVIDER_UNAVAILABLE,
    RATE_LIMITED,
    SESSION_NOT_FOUND,
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


class _SessionState:
    __slots__ = (
        "session_id",
        "subject",
        "opened_at",
        "expires_at",
        "last_sequence",
        "segments",
        "total_bytes",
        "in_flight",
        "ended",
    )

    def __init__(self, session_id: str, subject: str, opened: float, ttl_ms: int) -> None:
        self.session_id = session_id
        self.subject = subject
        self.opened_at = opened
        self.expires_at = opened + ttl_ms / 1000.0
        self.last_sequence = 0
        self.segments = 0
        self.total_bytes = 0
        self.in_flight = 0
        self.ended = False


class IncrementalDictationService:
    """dictation.incremental.v1 session + segment use case."""

    _MAX_SESSIONS = 10_000

    def __init__(
        self,
        *,
        port,
        max_session_ms: int,
        max_segments: int,
        max_segment_duration_ms: int,
        max_segment_bytes: int,
        max_total_bytes: int,
        session_ttl_ms: int,
        rate_limit_per_minute: int,
        max_in_flight: int,
        clock: Callable[[], float] = time.monotonic,
        session_id_factory: Callable[[], str] | None = None,
    ) -> None:
        if port is None:
            raise ValueError("IncrementalDictationService requires a port")
        self._port = port
        self._max_session_ms = int(max_session_ms)
        self._max_segments = int(max_segments)
        self._max_segment_duration_ms = int(max_segment_duration_ms)
        self._max_segment_bytes = int(max_segment_bytes)
        self._max_total_bytes = int(max_total_bytes)
        self._session_ttl_ms = int(session_ttl_ms)
        self._rate_limit = max(1, int(rate_limit_per_minute))
        self._max_in_flight = max(1, int(max_in_flight))
        self._clock = clock
        self._session_id_factory = session_id_factory or (
            lambda: str(uuid.uuid4())
        )
        self._sessions: dict[str, _SessionState] = {}
        self._rate_windows: dict[str, tuple[float, int]] = {}
        self._lock = threading.Lock()

    @property
    def contract_name(self) -> str:
        return INCREMENTAL_CONTRACT_NAME

    @property
    def contract_version(self) -> str:
        return INCREMENTAL_CONTRACT_VERSION

    def open_session(
        self, access_context
    ) -> IncrementalDictationSession:
        if not has_delia_access(access_context):
            raise DictationError(
                FORBIDDEN, "delia.access is required for dictation"
            )
        subject = (getattr(access_context, "user_id", "") or "").strip() or "unknown"
        now = self._clock()
        with self._lock:
            self._purge(now)
            if not self._allow(subject, now):
                raise DictationError(
                    RATE_LIMITED, "dictation session rate limit exceeded"
                )
            session_id = self._session_id_factory()
            self._sessions[session_id] = _SessionState(
                session_id, subject, now, self._session_ttl_ms
            )
        return IncrementalDictationSession(
            session_id=session_id,
            max_session_ms=self._max_session_ms,
            max_segments=self._max_segments,
            max_segment_duration_ms=self._max_segment_duration_ms,
        )

    def end_session(self, session_id: str, access_context) -> None:
        subject = (getattr(access_context, "user_id", "") or "").strip()
        with self._lock:
            state = self._sessions.get(session_id)
            if state is None:
                return  # idempotent close
            if state.subject != (subject or "unknown"):
                raise DictationError(FORBIDDEN, "session belongs to another user")
            state.ended = True
            self._sessions.pop(session_id, None)

    def stream_segment(
        self,
        *,
        session_id: str,
        access_context,
        segment_id: str,
        sequence: int,
        audio_bytes: bytes,
        mime_type: str,
        duration_ms: int,
        language_hint: str = SUPPORTED_LANGUAGE,
    ) -> Iterator[str]:
        """Admit a segment (synchronously) and return its real event stream.

        Admission is eager: AuthZ/session/sequence/bounds failures raise
        DictationError before any byte is emitted, so the HTTP boundary
        can still answer a typed error status. The returned iterator
        yields NDJSON event lines (started → partial* → final|error).
        """
        provider_format, request = self._admit_segment(
            session_id=session_id,
            access_context=access_context,
            segment_id=segment_id,
            sequence=sequence,
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            duration_ms=duration_ms,
            language_hint=language_hint,
        )
        return self._events(
            session_id=session_id,
            segment_id=segment_id,
            sequence=sequence,
            provider_format=provider_format,
            request=request,
        )

    def _events(
        self,
        *,
        session_id: str,
        segment_id: str,
        sequence: int,
        provider_format: str,
        request: SpeechTranscriptionRequest,
    ) -> Iterator[str]:
        yield json.dumps(
            {
                "type": EVENT_STARTED,
                "session_id": session_id,
                "segment_id": segment_id,
                "sequence": sequence,
                "revision": 0,
            },
            ensure_ascii=False,
        )
        try:
            yield from self._provider_events(
                session_id=session_id,
                segment_id=segment_id,
                sequence=sequence,
                provider_format=provider_format,
                request=request,
            )
        finally:
            with self._lock:
                state = self._sessions.get(session_id)
                if state is not None:
                    state.in_flight = max(0, state.in_flight - 1)

    def _admit_segment(
        self,
        *,
        session_id: str,
        access_context,
        segment_id: str,
        sequence: int,
        audio_bytes: bytes,
        mime_type: str,
        duration_ms: int,
        language_hint: str,
    ) -> tuple[str, SpeechTranscriptionRequest]:
        if not has_delia_access(access_context):
            raise DictationError(
                FORBIDDEN, "delia.access is required for dictation"
            )
        subject = (getattr(access_context, "user_id", "") or "").strip() or "unknown"
        now = self._clock()
        with self._lock:
            self._purge(now)
            state = self._sessions.get(session_id)
            if state is None or state.ended or now >= state.expires_at:
                self._sessions.pop(session_id, None)
                raise DictationError(
                    SESSION_NOT_FOUND, "dictation session is not active"
                )
            if state.subject != subject:
                raise DictationError(
                    FORBIDDEN, "session belongs to another user"
                )
            if (
                not isinstance(sequence, int)
                or isinstance(sequence, bool)
                or sequence <= state.last_sequence
            ):
                raise DictationError(
                    INVALID_SEQUENCE,
                    "segment sequence must strictly increase",
                )
            if state.segments >= self._max_segments:
                raise DictationError(
                    RATE_LIMITED, "session segment bound reached"
                )
            if state.in_flight >= self._max_in_flight:
                raise DictationError(
                    RATE_LIMITED, "too many concurrent segments"
                )
            if (language_hint or "").strip() != SUPPORTED_LANGUAGE:
                raise DictationError(
                    UNSUPPORTED_LANGUAGE,
                    "only pt-BR dictation is supported by this contract",
                )
            provider_format = AUDIO_MIME_TO_FORMAT.get(normalize_mime(mime_type))
            if provider_format is None:
                raise DictationError(
                    UNSUPPORTED_MEDIA, "audio mime type is not supported"
                )
            if (
                not isinstance(duration_ms, int)
                or isinstance(duration_ms, bool)
                or duration_ms <= 0
                or duration_ms > self._max_segment_duration_ms
            ):
                raise DictationError(
                    DURATION_EXCEEDED,
                    "segment duration exceeds contract limits",
                )
            if not isinstance(audio_bytes, (bytes, bytearray)) or not audio_bytes:
                raise DictationError(UNSUPPORTED_MEDIA, "audio payload is empty")
            if len(audio_bytes) > self._max_segment_bytes:
                raise DictationError(
                    PAYLOAD_TOO_LARGE,
                    "segment payload exceeds contract limits",
                )
            if state.total_bytes + len(audio_bytes) > self._max_total_bytes:
                raise DictationError(
                    PAYLOAD_TOO_LARGE,
                    "session audio budget exceeded",
                )
            state.last_sequence = sequence
            state.segments += 1
            state.total_bytes += len(audio_bytes)
            state.in_flight += 1
        return provider_format, SpeechTranscriptionRequest(
            audio_bytes=bytes(audio_bytes),
            provider_format=provider_format,
            language_hint=SUPPORTED_LANGUAGE,
            timeout_hint_ms=None,
        )

    def _provider_events(
        self,
        *,
        session_id: str,
        segment_id: str,
        sequence: int,
        provider_format: str,
        request: SpeechTranscriptionRequest,
    ) -> Iterator[str]:
        revision = 0
        last_text = ""
        try:
            for snapshot in self._port.stream_transcribe(request):
                text = str(snapshot or "")
                if not text or text == last_text:
                    continue
                revision += 1
                last_text = text
                yield json.dumps(
                    {
                        "type": EVENT_PARTIAL,
                        "session_id": session_id,
                        "segment_id": segment_id,
                        "sequence": sequence,
                        "revision": revision,
                        "is_final": False,
                        "text": text,
                    },
                    ensure_ascii=False,
                )
        except DictationError as exc:
            yield json.dumps(
                {
                    "type": EVENT_ERROR,
                    "session_id": session_id,
                    "segment_id": segment_id,
                    "sequence": sequence,
                    "code": exc.code,
                },
                ensure_ascii=False,
            )
            return
        except Exception:
            yield json.dumps(
                {
                    "type": EVENT_ERROR,
                    "session_id": session_id,
                    "segment_id": segment_id,
                    "sequence": sequence,
                    "code": PROVIDER_UNAVAILABLE,
                },
                ensure_ascii=False,
            )
            return
        normalized = last_text.strip()
        if not normalized:
            yield json.dumps(
                {
                    "type": EVENT_ERROR,
                    "session_id": session_id,
                    "segment_id": segment_id,
                    "sequence": sequence,
                    "code": "empty_transcription",
                },
                ensure_ascii=False,
            )
            return
        yield json.dumps(
            {
                "type": EVENT_FINAL,
                "session_id": session_id,
                "segment_id": segment_id,
                "sequence": sequence,
                "revision": max(1, revision),
                "is_final": True,
                "text": normalized,
                "language": SUPPORTED_LANGUAGE,
            },
            ensure_ascii=False,
        )

    def _allow(self, subject: str, now: float) -> bool:
        start, count = self._rate_windows.get(subject, (now, 0))
        if now - start >= 60.0:
            start, count = now, 0
        if count >= self._rate_limit:
            self._rate_windows[subject] = (start, count)
            return False
        self._rate_windows[subject] = (start, count + 1)
        return True

    def _purge(self, now: float) -> None:
        expired = [
            key
            for key, state in self._sessions.items()
            if state.ended or now >= state.expires_at
        ]
        for key in expired:
            self._sessions.pop(key, None)
        if len(self._sessions) > self._MAX_SESSIONS:
            # Bounded memory: evict the oldest sessions first.
            for key in sorted(
                self._sessions, key=lambda k: self._sessions[k].opened_at
            )[: len(self._sessions) - self._MAX_SESSIONS]:
                self._sessions.pop(key, None)


__all__ = ["IncrementalDictationService"]
