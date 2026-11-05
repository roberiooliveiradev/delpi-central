"""G7/G6 residual (doc 265 §2): REAL local HTTP server streaming test.

`deadline_http_post` returns the response after the governed Session
is closed — the streamed response must stay readable, SSE trickles
below the read-inactivity window must respect the ABSOLUTE deadline,
and a mid-stream stall must die at the deadline.
"""

from __future__ import annotations

import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from app.application.dictation.errors import PROVIDER_TIMEOUT, DictationError
from app.application.ports.speech_transcription_port import (
    SpeechTranscriptionRequest,
)
from app.infrastructure.model_invocation.openai_compatible_transcription_adapter import (
    OpenAICompatibleTranscriptionAdapter,
)


def _sse(text: str) -> bytes:
    import json

    payload = json.dumps(
        {"choices": [{"delta": {"content": text}}]}, ensure_ascii=False
    )
    return ("data: " + payload + "\n\n").encode("utf-8")


class _TrickleHandler(BaseHTTPRequestHandler):
    chunks: list[bytes] = []
    stall_seconds: float = 0.0
    trickle_seconds: float = 0.0

    def log_message(self, *args):
        pass

    def do_POST(self):
        chunks = list(type(self).chunks)
        stall = type(self).stall_seconds
        trickle = type(self).trickle_seconds
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for i, chunk in enumerate(chunks):
            if i == len(chunks) - 1 and stall:
                time.sleep(stall)
            if trickle:
                time.sleep(trickle)
            try:
                self.wfile.write(chunk)
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                return


@pytest.fixture()
def server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _TrickleHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd, f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def _adapter(url: str, timeout: float):
    return OpenAICompatibleTranscriptionAdapter(
        base_url=url,
        api_key="k",
        model="m",
        timeout_seconds=timeout,
    )


def _req():
    return SpeechTranscriptionRequest(
        audio_bytes=b"wav", provider_format="wav", language_hint="pt-BR"
    )


def test_real_stream_complete_after_session_close(server):
    """The response returned by deadline_http_post stays readable after
    its governed Session is closed — real SSE over a local socket."""
    httpd, url = server
    _TrickleHandler.chunks = [_sse("Alô, alô"), b"data: [DONE]\n\n"]
    _TrickleHandler.stall_seconds = 0
    _TrickleHandler.trickle_seconds = 0
    out = list(_adapter(url, 10.0).stream_transcribe(_req()))
    assert out == ["Alô, alô"]


def test_real_stream_slow_trickle_within_deadline(server):
    """Bytes trickling slower than the read inactivity window but
    inside the absolute deadline still complete."""
    httpd, url = server
    _TrickleHandler.chunks = [_sse("a"), _sse("b"), b"data: [DONE]\n\n"]
    _TrickleHandler.stall_seconds = 0
    _TrickleHandler.trickle_seconds = 0.3
    out = list(_adapter(url, 10.0).stream_transcribe(_req()))
    assert out == ["a", "ab"]


def test_real_stream_mid_stall_dies_at_absolute_deadline(server):
    """A mid-stream stall is killed at the ABSOLUTE deadline — bytes
    arriving within the inactivity window cannot stretch it."""
    httpd, url = server
    _TrickleHandler.chunks = [_sse("partial"), b"data: [DONE]\n\n"]
    _TrickleHandler.stall_seconds = 4.0
    _TrickleHandler.trickle_seconds = 0
    started = time.monotonic()
    with pytest.raises(DictationError) as exc:
        list(_adapter(url, 1.0).stream_transcribe(_req()))
    elapsed = time.monotonic() - started
    assert exc.value.code == PROVIDER_TIMEOUT
    assert elapsed < 3.0  # died at ~1s deadline, not the 4s stall


def test_real_stream_utf8_split_across_chunks(server):
    """A UTF-8 char split across chunks decodes intact over a real socket."""
    httpd, url = server
    payload = _sse("Alô ô")
    mid = payload.index("ô".encode("utf-8")) + 1
    _TrickleHandler.chunks = [
        payload[:mid], payload[mid:], b"data: [DONE]\n\n"
    ]
    _TrickleHandler.stall_seconds = 0
    _TrickleHandler.trickle_seconds = 0
    out = list(_adapter(url, 10.0).stream_transcribe(_req()))
    assert out == ["Alô ô"]
