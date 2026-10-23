"""dictation.incremental.v1 — wire-protocol hardening tests (VD-F06 rework).

RED-first for the production incidents:
- Incident B (mojibake): provider SSE is UTF-8 by spec, but ``requests``
  decodes ``text/event-stream`` as ISO-8859-1 when no charset is given —
  ``Alô`` arrived as ``AlÃ´``. The adapter must decode SSE bytes as UTF-8.
- Multibyte safety: a UTF-8 sequence may split across iter_content
  chunks; line framing must happen on bytes so characters stay intact.
- Incident C (empty_transcription): an empty/failed segment is
  segment-scoped — the session must keep admitting following segments.
"""

from __future__ import annotations

import io
import json

import pytest
import requests

from app.application.dictation.errors import DictationError
from app.application.dictation.incremental_dictation_session import (
    IncrementalDictationService,
)
from app.application.platform_access import PlatformAccessContext
from app.application.ports.speech_transcription_port import (
    SpeechTranscriptionRequest,
)
from app.infrastructure.model_invocation.openai_compatible_transcription_adapter import (
    OpenAICompatibleTranscriptionAdapter,
)


def _ctx(user_id: str = "u-1") -> PlatformAccessContext:
    return PlatformAccessContext(
        user_id=user_id,
        name="User",
        email="u@x.dev",
        effective_permissions=("delia.access",),
    )


def _sse_response(chunks: list[bytes], status: int = 200) -> requests.Response:
    """Real requests.Response over raw bytes — same decoding path as prod."""
    body = b"".join(chunks)

    class _Raw(io.BytesIO):
        def stream(self, chunk_size, decode_content=True):
            yield from iter(chunks)

    response = requests.Response()
    response.status_code = status
    response.headers["Content-Type"] = "text/event-stream"
    response.raw = _Raw(body)
    response.encoding = requests.utils.get_encoding_from_headers(
        response.headers
    )
    return response


def _sse_chunk(text: str) -> bytes:
    payload = json.dumps(
        {"choices": [{"delta": {"content": text}}]}, ensure_ascii=False
    )
    return ("data: " + payload + "\n\n").encode("utf-8")


def _adapter() -> OpenAICompatibleTranscriptionAdapter:
    return OpenAICompatibleTranscriptionAdapter(
        base_url="https://provider.example/api/v1",
        api_key="test-key",  # noqa: S106 — fixture value
        model="vendor/model",
        timeout_seconds=30.0,
    )


def _request() -> SpeechTranscriptionRequest:
    return SpeechTranscriptionRequest(
        audio_bytes=b"wav",
        provider_format="wav",
        language_hint="pt-BR",
        timeout_hint_ms=None,
    )


def test_sse_utf8_ptbr_not_corrupted_by_latin1_default(monkeypatch):
    """RED: 'Alô, alô' must not arrive as 'AlÃ´, alÃ´' (PO incident B)."""
    adapter = _adapter()
    response = _sse_response([_sse_chunk("Alô, alô"), b"data: [DONE]\n\n"])
    monkeypatch.setattr(requests, "post", lambda *a, **k: response)
    snapshots = list(adapter.stream_transcribe(_request()))
    assert snapshots == ["Alô, alô"]


def test_sse_utf8_full_accent_set(monkeypatch):
    text = "áàâãéêíóôõúç — Transcrição correta"
    adapter = _adapter()
    response = _sse_response([_sse_chunk(text), b"data: [DONE]\n\n"])
    monkeypatch.setattr(requests, "post", lambda *a, **k: response)
    snapshots = list(adapter.stream_transcribe(_request()))
    assert snapshots == [text]


def test_sse_multibyte_split_across_chunks_survives(monkeypatch):
    """A UTF-8 char split between iter_content chunks stays intact."""
    payload = _sse_chunk("Alô ô ô")
    mid = payload.index("ô".encode("utf-8")) + 1  # inside the 2-byte char
    adapter = _adapter()
    response = _sse_response(
        [payload[:mid], payload[mid:], b"data: [DONE]\n\n"]
    )
    monkeypatch.setattr(requests, "post", lambda *a, **k: response)
    snapshots = list(adapter.stream_transcribe(_request()))
    assert snapshots == ["Alô ô ô"]


def test_sse_json_split_across_chunks_survives(monkeypatch):
    """A single SSE event split anywhere across chunks still parses."""
    payload = _sse_chunk("transcrição parcial")
    cut = len(payload) // 2
    adapter = _adapter()
    response = _sse_response(
        [payload[:cut], payload[cut:], b"data: [DONE]\n\n"]
    )
    monkeypatch.setattr(requests, "post", lambda *a, **k: response)
    snapshots = list(adapter.stream_transcribe(_request()))
    assert snapshots == ["transcrição parcial"]


# ------------------------------------------------------------------
# Incident C — empty/failed segment is segment-scoped; the session
# keeps admitting following segments (contract continuity).
# ------------------------------------------------------------------


class _EmptyThenOkPort:
    adapter_kind = "TEST"

    def __init__(self):
        self.calls = 0

    def stream_transcribe(self, request):
        self.calls += 1
        if self.calls == 1:
            return
            yield  # pragma: no cover
        yield "continua ditando"


def _service(port) -> IncrementalDictationService:
    return IncrementalDictationService(
        port=port,
        max_session_ms=300_000,
        max_segments=120,
        max_segment_duration_ms=15_000,
        max_segment_bytes=1_500_000,
        max_total_bytes=8_000_000,
        session_ttl_ms=360_000,
        rate_limit_per_minute=10,
        max_in_flight=4,
        clock=lambda: 1000.0,
    )


def _collect(gen):
    return [json.loads(line) for line in gen]


def test_empty_segment_is_scoped_and_session_continues():
    svc = _service(_EmptyThenOkPort())
    session = svc.open_session(_ctx())
    seg1 = _collect(
        svc.stream_segment(
            session_id=session.session_id,
            access_context=_ctx(),
            segment_id="seg-1",
            sequence=1,
            audio_bytes=b"silence",
            mime_type="audio/wav",
            duration_ms=4000,
        )
    )
    assert seg1[-1]["type"] == "error"
    assert seg1[-1]["code"] == "empty_transcription"
    # Segment-scoped: next segment is admitted and streams normally.
    seg2 = _collect(
        svc.stream_segment(
            session_id=session.session_id,
            access_context=_ctx(),
            segment_id="seg-2",
            sequence=2,
            audio_bytes=b"speech",
            mime_type="audio/wav",
            duration_ms=4000,
        )
    )
    assert seg2[-1]["type"] == "final"
    assert seg2[-1]["text"] == "continua ditando"


class _TimeoutPort:
    adapter_kind = "TEST"

    def stream_transcribe(self, request):
        raise DictationError("provider_timeout", "timed out")
        yield  # pragma: no cover


def test_provider_timeout_segment_error_does_not_kill_session():
    svc = _service(_TimeoutPort())
    session = svc.open_session(_ctx())
    seg1 = _collect(
        svc.stream_segment(
            session_id=session.session_id,
            access_context=_ctx(),
            segment_id="seg-1",
            sequence=1,
            audio_bytes=b"speech",
            mime_type="audio/wav",
            duration_ms=4000,
        )
    )
    assert seg1[-1]["type"] == "error"
    assert seg1[-1]["code"] == "provider_timeout"
    seg2 = _collect(
        svc.stream_segment(
            session_id=session.session_id,
            access_context=_ctx(),
            segment_id="seg-2",
            sequence=2,
            audio_bytes=b"speech",
            mime_type="audio/wav",
            duration_ms=4000,
        )
    )
    assert seg2[-1]["type"] == "error"  # deterministic fail port
    # The session itself stayed alive for the second admission.
