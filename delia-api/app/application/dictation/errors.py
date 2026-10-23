"""Dictation transcription errors — semantic codes, no provider leakage."""

from __future__ import annotations


class DictationError(Exception):
    """Bounded application error for dictation transcription."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


INVALID_REQUEST = "invalid_request"
FORBIDDEN = "forbidden"
UNSUPPORTED_MEDIA = "unsupported_media"
UNSUPPORTED_LANGUAGE = "unsupported_language"
DURATION_EXCEEDED = "duration_exceeded"
PAYLOAD_TOO_LARGE = "payload_too_large"
RATE_LIMITED = "rate_limited"
TRANSCRIPTION_UNAVAILABLE = "transcription_unavailable"
PROVIDER_UNAVAILABLE = "provider_unavailable"
PROVIDER_REJECTED = "provider_rejected"
PROVIDER_TIMEOUT = "provider_timeout"
EMPTY_TRANSCRIPTION = "empty_transcription"
SESSION_NOT_FOUND = "session_not_found"
INVALID_SEQUENCE = "invalid_sequence"
INTERNAL_ERROR = "internal_error"
