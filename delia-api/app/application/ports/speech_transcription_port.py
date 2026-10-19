"""Application-facing port for provider-neutral speech transcription.

VD-F03 (spec 119 §0): audio → untrusted text only. The port carries no
provider vocabulary, no transport mechanics, and no authority — the
adapter maps the provider-neutral `provider_format` token to whatever
mechanism an approved provider requires.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class SpeechTranscriptionRequest:
    """Provider-neutral transcription input."""

    audio_bytes: bytes
    provider_format: str
    language_hint: str
    timeout_hint_ms: int | None = None


class SpeechTranscriptionPort(Protocol):
    """One-shot audio→text transcription. Text is untrusted input."""

    @property
    def adapter_kind(self) -> str:
        """Provider family token (e.g. OPENAI_COMPATIBLE_AUDIO)."""
        ...

    def transcribe(self, request: SpeechTranscriptionRequest) -> str:
        """Return transcribed text; may be empty (postcondition fails)."""
        ...
