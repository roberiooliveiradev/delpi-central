"""VD-F03 dictation.transcription.v1 — contract, use case and route tests.

Covers AuthN/AuthZ, MIME allowlist, limits, rate limit, typed errors,
postcondition (empty transcript), and the status admission surface.
Audio/transcript content is never asserted into logs — only metadata.
"""

from __future__ import annotations

import base64

import pytest

from app.application.dictation.contracts import (
    DictationTranscriptionRequest,
)
from app.application.dictation.errors import (
    DictationError,
    PROVIDER_TIMEOUT,
    PROVIDER_UNAVAILABLE,
    RATE_LIMITED,
)
from app.application.dictation.transcribe_dictation import (
    TranscribeDictation,
)
from app.application.platform_access import PlatformAccessContext
from app.create_app import create_app

STATUS_PATH = "/dictation/status"
TRANSCRIBE_PATH = "/dictation/transcriptions"


def _context(
    permissions: tuple[str, ...] = ("delia.access",),
    is_superadmin: bool = False,
    user_id: str = "u1",
) -> PlatformAccessContext:
    return PlatformAccessContext(
        user_id=user_id,
        name="User",
        email="u@example.com",
        effective_permissions=permissions,
        is_superadmin=is_superadmin,
    )


class _Provider:
    def __init__(self, context: PlatformAccessContext | None = None):
        self._context = context or _context()

    def resolve(self, bearer_token: str):
        return self._context


class _FakePort:
    def __init__(self, text="texto transcrito", exc=None):
        self._text = text
        self._exc = exc
        self.calls = []

    def transcribe(self, request):
        self.calls.append(request)
        if self._exc is not None:
            raise self._exc
        return self._text


def _handler(port=None, **kwargs):
    return TranscribeDictation(
        port=port or _FakePort(),
        max_audio_bytes=kwargs.get("max_audio_bytes", 1024),
        max_duration_ms=kwargs.get("max_duration_ms", 10_000),
        rate_limit_per_minute=kwargs.get("rate_limit_per_minute", 3),
        clock=kwargs.get("clock", _FakeClock()),
    )


class _FakeClock:
    def __init__(self, now: float = 1000.0):
        self.now = now

    def __call__(self) -> float:
        return self.now


def _client(context=None, handler_marker=None, limits=None):
    kwargs = {}
    if handler_marker is not None:
        kwargs["dictation_transcription_handler"] = handler_marker
    app = create_app(
        testing=True,
        platform_access_provider=_Provider(context),
        **kwargs,
    )
    if limits:
        app.config["DICTATION_LIMITS"] = limits
    return app.test_client()


def _payload(**overrides):
    body = {
        "audio_base64": base64.b64encode(b"fake-audio").decode(),
        "mime_type": "audio/webm;codecs=opus",
        "duration_ms": 1200,
        "language_hint": "pt-BR",
    }
    body.update(overrides)
    return body


def _post(client, body=None, headers=None):
    return client.post(
        TRANSCRIBE_PATH,
        json=body,
        headers=headers or {"Authorization": "Bearer t"},
    )


# ---------------- use case ----------------


def test_use_case_returns_typed_result_and_maps_mime():
    port = _FakePort("  Mostre os indicadores.  ")
    handler = _handler(
        port,
        clock=lambda: 1000.0,
    )
    result = handler.execute(
        DictationTranscriptionRequest(
            access_context=_context(),
            audio_bytes=b"audio",
            mime_type="Audio/WebM;Codecs=Opus",
            duration_ms=900,
        )
    )
    assert result.text == "Mostre os indicadores."
    assert result.language == "pt-BR"
    assert result.transcription_id
    assert port.calls[0].provider_format == "webm"


def test_use_case_denies_without_delia_access():
    handler = _handler()
    with pytest.raises(DictationError) as exc:
        handler.execute(
            DictationTranscriptionRequest(
                access_context=_context(permissions=("other.permission",)),
                audio_bytes=b"audio",
                mime_type="audio/webm",
                duration_ms=100,
            )
        )
    assert exc.value.code == "forbidden"


def test_use_case_denies_without_context():
    handler = _handler()
    with pytest.raises(DictationError) as exc:
        handler.execute(
            DictationTranscriptionRequest(
                access_context=None,
                audio_bytes=b"audio",
                mime_type="audio/webm",
                duration_ms=100,
            )
        )
    assert exc.value.code == "forbidden"


def test_use_case_rejects_unsupported_mime():
    with pytest.raises(DictationError) as exc:
        _handler().execute(
            DictationTranscriptionRequest(
                access_context=_context(),
                audio_bytes=b"audio",
                mime_type="audio/flac",
                duration_ms=100,
            )
        )
    assert exc.value.code == "unsupported_media"


def test_use_case_rejects_unsupported_language():
    with pytest.raises(DictationError) as exc:
        _handler().execute(
            DictationTranscriptionRequest(
                access_context=_context(),
                audio_bytes=b"audio",
                mime_type="audio/webm",
                duration_ms=100,
                language_hint="en-US",
            )
        )
    assert exc.value.code == "unsupported_language"


def test_use_case_rejects_duration_over_limit():
    with pytest.raises(DictationError) as exc:
        _handler().execute(
            DictationTranscriptionRequest(
                access_context=_context(),
                audio_bytes=b"audio",
                mime_type="audio/webm",
                duration_ms=10_001,
            )
        )
    assert exc.value.code == "duration_exceeded"


def test_use_case_rejects_empty_and_oversized_audio():
    with pytest.raises(DictationError) as exc:
        _handler().execute(
            DictationTranscriptionRequest(
                access_context=_context(),
                audio_bytes=b"",
                mime_type="audio/webm",
                duration_ms=100,
            )
        )
    assert exc.value.code == "unsupported_media"
    with pytest.raises(DictationError) as exc:
        _handler().execute(
            DictationTranscriptionRequest(
                access_context=_context(),
                audio_bytes=b"x" * 1025,
                mime_type="audio/webm",
                duration_ms=100,
            )
        )
    assert exc.value.code == "payload_too_large"


def test_use_case_rate_limits_per_user():
    clock = _FakeClock()
    handler = _handler(rate_limit_per_minute=2, clock=clock)
    req = DictationTranscriptionRequest(
        access_context=_context(),
        audio_bytes=b"audio",
        mime_type="audio/webm",
        duration_ms=100,
    )
    handler.execute(req)
    handler.execute(req)
    with pytest.raises(DictationError) as exc:
        handler.execute(req)
    assert exc.value.code == RATE_LIMITED
    # Window rollover restores capacity.
    clock.now += 61.0
    handler.execute(req)


def test_use_case_rate_limit_is_per_user_not_global():
    clock = _FakeClock()
    handler = _handler(rate_limit_per_minute=1, clock=clock)
    handler.execute(
        DictationTranscriptionRequest(
            access_context=_context(user_id="u1"),
            audio_bytes=b"audio",
            mime_type="audio/webm",
            duration_ms=100,
        )
    )
    # A different user keeps their own window.
    handler.execute(
        DictationTranscriptionRequest(
            access_context=_context(user_id="u2"),
            audio_bytes=b"audio",
            mime_type="audio/webm",
            duration_ms=100,
        )
    )


def test_use_case_empty_transcript_fails_postcondition():
    port = _FakePort("   ")
    with pytest.raises(DictationError) as exc:
        _handler(port=port).execute(
            DictationTranscriptionRequest(
                access_context=_context(),
                audio_bytes=b"audio",
                mime_type="audio/webm",
                duration_ms=100,
            )
        )
    assert exc.value.code == "empty_transcription"


def test_use_case_propagates_typed_provider_errors():
    port = _FakePort(exc=DictationError(PROVIDER_TIMEOUT, "boom"))
    with pytest.raises(DictationError) as exc:
        _handler(port=port).execute(
            DictationTranscriptionRequest(
                access_context=_context(),
                audio_bytes=b"audio",
                mime_type="audio/webm",
                duration_ms=100,
            )
        )
    assert exc.value.code == PROVIDER_TIMEOUT


def test_use_case_maps_unexpected_port_errors_fail_closed():
    port = _FakePort(exc=RuntimeError("kaboom"))
    with pytest.raises(DictationError) as exc:
        _handler(port=port).execute(
            DictationTranscriptionRequest(
                access_context=_context(),
                audio_bytes=b"audio",
                mime_type="audio/webm",
                duration_ms=100,
            )
        )
    assert exc.value.code == PROVIDER_UNAVAILABLE


# ---------------- HTTP boundary ----------------


def test_status_reports_unavailable_without_config():
    client = _client()
    response = client.get(
        STATUS_PATH, headers={"Authorization": "Bearer t"}
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["available"] is False
    assert body["contract_version"] == "1"
    assert body["language"] == "pt-BR"


def test_status_reports_available_with_handler_and_limits():
    client = _client(
        handler_marker=_handler(),
        limits={"max_audio_bytes": 4096, "max_duration_ms": 60000},
    )
    response = client.get(
        STATUS_PATH, headers={"Authorization": "Bearer t"}
    )
    body = response.get_json()
    assert body["available"] is True
    assert body["max_audio_bytes"] == 4096
    assert body["max_duration_ms"] == 60000


def test_transcribe_requires_authentication():
    client = _client(handler_marker=_handler())
    assert client.post(TRANSCRIBE_PATH, json=_payload()).status_code == 401


def test_transcribe_success_returns_text():
    port = _FakePort("Mostre os indicadores.")
    client = _client(handler_marker=_handler(port=port))
    response = _post(client, _payload())
    assert response.status_code == 200
    body = response.get_json()
    assert body["text"] == "Mostre os indicadores."
    assert body["language"] == "pt-BR"
    assert body["transcription_id"]


def test_transcribe_rejects_non_json_and_unknown_keys():
    client = _client(handler_marker=_handler())
    response = client.post(
        TRANSCRIBE_PATH,
        data="not json",
        content_type="application/json",
        headers={"Authorization": "Bearer t"},
    )
    assert response.status_code == 400
    response = _post(client, _payload(extra_field="x"))
    assert response.status_code == 400
    assert response.get_json()["code"] == "invalid_request"


def test_transcribe_rejects_invalid_base64():
    client = _client(handler_marker=_handler())
    response = _post(client, _payload(audio_base64="###not-b64###"))
    assert response.status_code == 400
    assert response.get_json()["code"] == "invalid_request"


def test_transcribe_rejects_oversized_encoded_payload():
    client = _client(
        handler_marker=_handler(),
        limits={"max_audio_bytes": 8, "max_duration_ms": 10_000},
    )
    big = base64.b64encode(b"x" * 64).decode()
    response = _post(client, _payload(audio_base64=big))
    assert response.status_code == 413
    assert response.get_json()["code"] == "payload_too_large"


def test_transcribe_unsupported_media_is_415():
    client = _client(handler_marker=_handler())
    response = _post(client, _payload(mime_type="audio/flac"))
    assert response.status_code == 415
    assert response.get_json()["code"] == "unsupported_media"


def test_transcribe_forbidden_without_delia_access():
    client = _client(
        context=_context(permissions=("other.permission",)),
        handler_marker=_handler(),
    )
    response = _post(client, _payload())
    assert response.status_code == 403


def test_transcribe_unavailable_without_handler():
    client = _client()
    response = _post(client, _payload())
    assert response.status_code == 503
    assert response.get_json()["code"] == "transcription_unavailable"
