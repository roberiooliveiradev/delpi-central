"""Dictation transcription contracts — dictation.transcription.v1.

VD-F03 (spec 119 §0): converts ONE completed local voice-dictation
capture into editable, untrusted draft text. The transcript is user
input — never Evidence, FACT, permission, or authorization for ACT/
PREPARE/domain decisions/OT commands, and never auto-submitted.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.platform_access import PlatformAccessContext


DICTATION_CONTRACT_VERSION = "1"
SUPPORTED_LANGUAGE = "pt-BR"

# MIME allowlist (contract §2.3). Values map to the provider-neutral
# audio format vocabulary; an unlisted MIME is `unsupported_media`.
AUDIO_MIME_TO_FORMAT = {
    "audio/webm": "webm",
    "audio/webm;codecs=opus": "webm",
    "audio/ogg": "ogg",
    "audio/ogg;codecs=opus": "ogg",
    "audio/mp4": "mp4",
    "audio/wav": "wav",
    "audio/mpeg": "mp3",
}


def normalize_mime(mime_type: object) -> str:
    """Canonicalize a MIME token for allowlist lookup (case/space-tolerant)."""
    if not isinstance(mime_type, str):
        return ""
    return mime_type.strip().lower()


@dataclass(frozen=True, slots=True)
class DictationTranscriptionRequest:
    """Bounded request: raw captured audio plus declared metadata."""

    access_context: PlatformAccessContext | None
    audio_bytes: bytes
    mime_type: str
    duration_ms: int
    language_hint: str = SUPPORTED_LANGUAGE


@dataclass(frozen=True, slots=True)
class DictationTranscriptionResult:
    """Postcondition-proven result: non-empty editable text."""

    transcription_id: str
    text: str
    language: str


# ---------------------------------------------------------------------------
# dictation.incremental.v1 (VD-F06) — segmented live dictation sessions.
#
# The incremental contract is strictly additive over v1: one session binds
# ordered audio SEGMENTS captured while the user is still speaking. Each
# segment is a complete audio blob transcribed for real by the provider —
# partial events forward the provider's streamed response tokens (never
# fabricated text), and `final` closes the segment exactly once.
# ---------------------------------------------------------------------------

INCREMENTAL_CONTRACT_VERSION = "1"
INCREMENTAL_CONTRACT_NAME = "dictation.incremental.v1"

EVENT_STARTED = "started"
EVENT_PARTIAL = "partial"
EVENT_FINAL = "final"
EVENT_ERROR = "error"


@dataclass(frozen=True, slots=True)
class IncrementalDictationSession:
    """Admitted incremental session handle (in-process, TTL-bound)."""

    session_id: str
    max_session_ms: int
    max_segments: int
    max_segment_duration_ms: int


@dataclass(frozen=True, slots=True)
class IncrementalSegmentRequest:
    """One ordered audio segment inside an admitted session."""

    access_context: PlatformAccessContext | None
    session_id: str
    segment_id: str
    sequence: int
    audio_bytes: bytes
    mime_type: str
    duration_ms: int
    language_hint: str = SUPPORTED_LANGUAGE
