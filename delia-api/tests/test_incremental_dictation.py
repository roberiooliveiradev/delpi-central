"""dictation.incremental.v1 — session + streamed segment contract tests (VD-F06).

RED-first: proves the bounded session/segment lifecycle emits real
provider-streamed events (started/partial/final) over NDJSON while the
batch dictation.transcription.v1 surface stays untouched.
"""

from __future__ import annotations

import base64
import json

import pytest

from app.application.dictation.contracts import SUPPORTED_LANGUAGE
from app.application.dictation.errors import (
    FORBIDDEN,
    INVALID_SEQUENCE,
    RATE_LIMITED,
    SESSION_NOT_FOUND,
    UNSUPPORTED_MEDIA,
    DictationError,
)
from app.application.dictation.incremental_dictation_session import (
    IncrementalDictationService,
)
from app.application.platform_access import PlatformAccessContext


def _ctx(user_id: str = "u-1", allowed: bool = True) -> PlatformAccessContext:
    return PlatformAccessContext(
        user_id=user_id,
        name="User",
        email="u@x.dev",
        effective_permissions=("delia.access",) if allowed else (),
    )


class _FakeStreamPort:
    """Deterministic provider stream: cumulative snapshots."""

    adapter_kind = "TEST_STREAM"

    def __init__(self, chunks=("Mostre os ", "Mostre os indicadores")):
        self._chunks = chunks
        self.calls = 0

    def stream_transcribe(self, request):
        self.calls += 1
        acc = ""
        for chunk in self._chunks:
            acc = chunk
            yield acc


class _FailPort:
    adapter_kind = "TEST_FAIL"

    def stream_transcribe(self, request):
        raise DictationError("provider_unavailable", "provider down")
        yield  # pragma: no cover


def _service(port=None, **kwargs):
    defaults = dict(
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
    defaults.update(kwargs)
    return IncrementalDictationService(
        port=port or _FakeStreamPort(), **defaults
    )


def _collect(gen):
    return [json.loads(line) for line in gen]


def test_session_open_requires_delia_access():
    svc = _service()
    with pytest.raises(DictationError) as err:
        svc.open_session(_ctx(allowed=False))
    assert err.value.code == FORBIDDEN


def test_segment_stream_emits_started_partial_final():
    svc = _service()
    session = svc.open_session(_ctx())
    gen = svc.stream_segment(
        session_id=session.session_id,
        access_context=_ctx(),
        segment_id="seg-1",
        sequence=1,
        audio_bytes=b"wav-audio",
        mime_type="audio/wav",
        duration_ms=4200,
    )
    events = _collect(gen)
    assert events[0]["type"] == "started"
    assert events[0]["session_id"] == session.session_id
    assert events[0]["segment_id"] == "seg-1"
    partials = [e for e in events if e["type"] == "partial"]
    assert [p["revision"] for p in partials] == [1, 2]
    assert partials[-1]["text"] == "Mostre os indicadores"
    assert events[-1]["type"] == "final"
    assert events[-1]["is_final"] is True
    assert events[-1]["text"] == "Mostre os indicadores"
    assert events[-1]["language"] == SUPPORTED_LANGUAGE


def test_foreign_user_cannot_use_session():
    svc = _service()
    session = svc.open_session(_ctx("u-1"))
    with pytest.raises(DictationError) as err:
        svc.stream_segment(
            session_id=session.session_id,
            access_context=_ctx("u-2"),
            segment_id="seg-1",
            sequence=1,
            audio_bytes=b"x",
            mime_type="audio/wav",
            duration_ms=100,
        )
    assert err.value.code == FORBIDDEN


def test_unknown_session_rejected():
    svc = _service()
    with pytest.raises(DictationError) as err:
        svc.stream_segment(
            session_id="missing",
            access_context=_ctx(),
            segment_id="seg-1",
            sequence=1,
            audio_bytes=b"x",
            mime_type="audio/wav",
            duration_ms=100,
        )
    assert err.value.code == SESSION_NOT_FOUND


def test_out_of_order_and_duplicate_sequence_rejected():
    svc = _service()
    session = svc.open_session(_ctx())
    list(
        svc.stream_segment(
            session_id=session.session_id,
            access_context=_ctx(),
            segment_id="seg-2",
            sequence=2,
            audio_bytes=b"x",
            mime_type="audio/wav",
            duration_ms=100,
        )
    )
    for seq in (1, 2):
        with pytest.raises(DictationError) as err:
            svc.stream_segment(
                session_id=session.session_id,
                access_context=_ctx(),
                segment_id="seg-x",
                sequence=seq,
                audio_bytes=b"x",
                mime_type="audio/wav",
                duration_ms=100,
            )
        assert err.value.code == INVALID_SEQUENCE


def test_session_rate_limited():
    svc = _service(rate_limit_per_minute=1)
    svc.open_session(_ctx())
    with pytest.raises(DictationError) as err:
        svc.open_session(_ctx())
    assert err.value.code == RATE_LIMITED


def test_unsupported_mime_rejected_before_streaming():
    svc = _service()
    session = svc.open_session(_ctx())
    with pytest.raises(DictationError) as err:
        svc.stream_segment(
            session_id=session.session_id,
            access_context=_ctx(),
            segment_id="seg-1",
            sequence=1,
            audio_bytes=b"x",
            mime_type="video/mp4",
            duration_ms=100,
        )
    assert err.value.code == UNSUPPORTED_MEDIA


def test_provider_failure_becomes_error_event_not_exception():
    svc = _service(port=_FailPort())
    session = svc.open_session(_ctx())
    events = _collect(
        svc.stream_segment(
            session_id=session.session_id,
            access_context=_ctx(),
            segment_id="seg-1",
            sequence=1,
            audio_bytes=b"x",
            mime_type="audio/wav",
            duration_ms=100,
        )
    )
    assert events[0]["type"] == "started"
    assert events[-1]["type"] == "error"
    assert events[-1]["code"] == "provider_unavailable"


def test_end_session_idempotent_and_invalidates():
    svc = _service()
    session = svc.open_session(_ctx())
    svc.end_session(session.session_id, _ctx())
    svc.end_session(session.session_id, _ctx())  # idempotent
    with pytest.raises(DictationError) as err:
        svc.stream_segment(
            session_id=session.session_id,
            access_context=_ctx(),
            segment_id="seg-9",
            sequence=9,
            audio_bytes=b"x",
            mime_type="audio/wav",
            duration_ms=100,
        )
    assert err.value.code == SESSION_NOT_FOUND


def test_session_expiry_by_ttl():
    now = [1000.0]
    svc = _service(clock=lambda: now[0], session_ttl_ms=5000)
    session = svc.open_session(_ctx())
    now[0] = 7000.0
    with pytest.raises(DictationError) as err:
        svc.stream_segment(
            session_id=session.session_id,
            access_context=_ctx(),
            segment_id="seg-1",
            sequence=1,
            audio_bytes=b"x",
            mime_type="audio/wav",
            duration_ms=100,
        )
    assert err.value.code == SESSION_NOT_FOUND


def test_session_and_segment_bounds_enforced():
    svc = _service(max_segments=1)
    session = svc.open_session(_ctx())
    list(
        svc.stream_segment(
            session_id=session.session_id,
            access_context=_ctx(),
            segment_id="seg-1",
            sequence=1,
            audio_bytes=b"x",
            mime_type="audio/wav",
            duration_ms=100,
        )
    )
    with pytest.raises(DictationError) as err:
        svc.stream_segment(
            session_id=session.session_id,
            access_context=_ctx(),
            segment_id="seg-2",
            sequence=2,
            audio_bytes=b"x",
            mime_type="audio/wav",
            duration_ms=100,
        )
    assert err.value.code == RATE_LIMITED


# ---------------- HTTP surface ----------------

STATUS_PATH = "/dictation/status"
SESSIONS_PATH = "/dictation/transcription-sessions"


class _Provider:
    def __init__(self, context: PlatformAccessContext | None = None):
        self._context = context or _ctx()

    def resolve(self, bearer_token: str):
        return self._context


def _client(context=None, service=None):
    from app.create_app import create_app

    app = create_app(
        testing=True,
        platform_access_provider=_Provider(context),
        dictation_incremental_service=service,
    )
    return app.test_client()


def _headers():
    return {"Authorization": "Bearer t"}


def _segment_body(**overrides):
    body = {
        "segment_id": "seg-1",
        "sequence": 1,
        "audio_base64": base64.b64encode(b"wav-bytes").decode(),
        "mime_type": "audio/wav",
        "duration_ms": 3200,
        "language_hint": "pt-BR",
    }
    body.update(overrides)
    return body


def test_status_reports_incremental_unavailable_when_not_wired():
    client = _client()
    res = client.get(STATUS_PATH, headers=_headers())
    assert res.status_code == 200
    data = res.get_json()
    assert data["contract_version"] == "1"
    assert data["incremental"]["available"] is False
    assert data["incremental"]["contract"] == "dictation.incremental.v1"
    assert data["incremental"]["contract_version"] == "1"


def test_status_reports_incremental_available_when_wired():
    client = _client(service=_service())
    res = client.get(STATUS_PATH, headers=_headers())
    assert res.status_code == 200
    assert res.get_json()["incremental"]["available"] is True


def test_session_endpoints_503_when_not_wired():
    client = _client()
    res = client.post(SESSIONS_PATH, headers=_headers())
    assert res.status_code == 503
    assert res.get_json()["code"] == "transcription_unavailable"


def test_route_open_stream_end_happy_path():
    client = _client(service=_service())
    res = client.post(SESSIONS_PATH, headers=_headers())
    assert res.status_code == 200
    session_id = res.get_json()["session_id"]
    assert res.get_json()["contract"] == "dictation.incremental.v1"
    assert res.get_json()["contract_version"] == "1"

    res = client.post(
        f"{SESSIONS_PATH}/{session_id}/segments",
        json=_segment_body(),
        headers=_headers(),
    )
    assert res.status_code == 200
    assert res.mimetype == "application/x-ndjson"
    lines = [
        json.loads(line)
        for line in res.data.decode().splitlines()
        if line.strip()
    ]
    assert lines[0]["type"] == "started"
    types = [line["type"] for line in lines]
    assert "partial" in types
    assert types[-1] == "final"

    res = client.post(
        f"{SESSIONS_PATH}/{session_id}/end", headers=_headers()
    )
    assert res.status_code == 200
    assert res.get_json()["ended"] is True

    res = client.post(
        f"{SESSIONS_PATH}/{session_id}/segments",
        json=_segment_body(sequence=2, segment_id="seg-2"),
        headers=_headers(),
    )
    assert res.status_code == 404
    assert res.get_json()["code"] == "session_not_found"


def test_route_open_requires_delia_access():
    client = _client(context=_ctx(allowed=False), service=_service())
    res = client.post(SESSIONS_PATH, headers=_headers())
    assert res.status_code == 403
    assert res.get_json()["code"] == "forbidden"


def test_route_segment_rejects_unknown_fields():
    client = _client(service=_service())
    res = client.post(SESSIONS_PATH, headers=_headers())
    session_id = res.get_json()["session_id"]
    res = client.post(
        f"{SESSIONS_PATH}/{session_id}/segments",
        json=_segment_body(extra="nope"),
        headers=_headers(),
    )
    assert res.status_code == 400
    assert res.get_json()["code"] == "invalid_request"


def test_route_segment_rejects_bad_base64_and_bad_sequence():
    client = _client(service=_service())
    res = client.post(SESSIONS_PATH, headers=_headers())
    session_id = res.get_json()["session_id"]
    res = client.post(
        f"{SESSIONS_PATH}/{session_id}/segments",
        json=_segment_body(audio_base64="!!not-b64!!"),
        headers=_headers(),
    )
    assert res.status_code == 400
    res = client.post(
        f"{SESSIONS_PATH}/{session_id}/segments",
        json=_segment_body(sequence="1"),
        headers=_headers(),
    )
    assert res.status_code == 400


def test_route_segment_duplicate_sequence_409():
    client = _client(service=_service())
    res = client.post(SESSIONS_PATH, headers=_headers())
    session_id = res.get_json()["session_id"]
    client.post(
        f"{SESSIONS_PATH}/{session_id}/segments",
        json=_segment_body(),
        headers=_headers(),
    )
    res = client.post(
        f"{SESSIONS_PATH}/{session_id}/segments",
        json=_segment_body(),
        headers=_headers(),
    )
    assert res.status_code == 409
    assert res.get_json()["code"] == "invalid_sequence"


def test_route_provider_error_emits_typed_ndjson_event():
    client = _client(service=_service(port=_FailPort()))
    res = client.post(SESSIONS_PATH, headers=_headers())
    session_id = res.get_json()["session_id"]
    res = client.post(
        f"{SESSIONS_PATH}/{session_id}/segments",
        json=_segment_body(),
        headers=_headers(),
    )
    assert res.status_code == 200
    lines = [
        json.loads(line)
        for line in res.data.decode().splitlines()
        if line.strip()
    ]
    assert lines[-1]["type"] == "error"
    assert lines[-1]["code"] == "provider_unavailable"
