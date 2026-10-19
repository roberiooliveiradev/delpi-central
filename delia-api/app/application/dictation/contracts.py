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
