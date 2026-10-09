"""R4.2 — OpenAI fileParams download_url fetcher guards.

The fetcher is the only allowed resolver of platform file references:
HTTPS + host allowlist + no redirects + byte cap. Arbitrary URLs fail
closed before any network call.
"""

from __future__ import annotations

from typing import Any

import pytest

from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.infrastructure.gateways import openai_file_gateway as mod
from tm_app.infrastructure.gateways.openai_file_gateway import (
    OpenAIFileGateway,
    sanitize_upload_filename,
)


def _fetch(url: str) -> dict[str, Any]:
    return OpenAIFileGateway().fetch(url)


def test_http_scheme_rejected():
    with pytest.raises(GptActionsError) as exc:
        _fetch("http://files.oaiusercontent.com/x")
    assert exc.value.data["error_code"] == "FILE_URL_NOT_ALLOWED"


def test_non_allowlisted_host_rejected():
    for url in (
        "https://evil.example.com/file",
        "https://files.oaiusercontent.com.evil.com/x",
        "https://169.254.169.254/latest/meta-data",
        "https://helpdesk-api.internal/tickets",
    ):
        with pytest.raises(GptActionsError) as exc:
            _fetch(url)
        assert exc.value.data["error_code"] == "FILE_URL_NOT_ALLOWED", url


def test_subdomain_of_allowlist_accepted():
    assert mod._host_allowed("cdn.files.oaiusercontent.com") is True
    assert mod._host_allowed("files.oaiusercontent.com.evil.com") is False


def test_empty_url_rejected():
    with pytest.raises(GptActionsError) as exc:
        _fetch("")
    assert exc.value.data["error_code"] == "FILE_URL_REQUIRED"


class _StreamResponse:
    def __init__(self, status: int, body: bytes, headers: dict | None = None):
        self.status_code = status
        self._body = body
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return None

    def iter_bytes(self):
        yield self._body


class _FakeClient:
    def __init__(self, response, recorder: list):
        self._response = response
        self._recorder = recorder

    def __call__(self, **kwargs):
        self._recorder.append(kwargs)
        return self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return None

    def stream(self, method, url):
        self._recorder.append(url)
        return self._response


@pytest.fixture
def _client(monkeypatch):
    recorder: list = []

    def install(response):
        monkeypatch.setattr(
            mod.httpx, "Client", _FakeClient(response, recorder)
        )
        return recorder

    return install


def test_fetch_returns_bytes_mime_filename(_client):
    recorder = _client(
        _StreamResponse(
            200,
            b"PNGDATA",
            {
                "content-type": "image/png",
                "content-disposition": 'attachment; filename="shot.png"',
            },
        )
    )
    out = _fetch("https://files.oaiusercontent.com/file-1?sig=x")
    assert out["content"] == b"PNGDATA"
    assert out["mime"] == "image/png"
    assert out["filename"] == "shot.png"
    # Redirects are never followed — the allowlist guard would be void.
    assert recorder[0]["follow_redirects"] is False


def test_fetch_too_large_fails_closed(_client):
    _client(
        _StreamResponse(200, b"x" * (mod.MAX_FILE_BYTES + 1), {})
    )
    with pytest.raises(GptActionsError) as exc:
        _fetch("https://files.oaiusercontent.com/big")
    assert exc.value.data["error_code"] == "FILE_TOO_LARGE"


def test_fetch_empty_file_rejected(_client):
    _client(_StreamResponse(200, b"", {}))
    with pytest.raises(GptActionsError) as exc:
        _fetch("https://files.oaiusercontent.com/empty")
    assert exc.value.data["error_code"] == "FILE_EMPTY"


def test_fetch_upstream_error_is_typed(_client):
    _client(_StreamResponse(503, b"", {}))
    with pytest.raises(GptActionsError) as exc:
        _fetch("https://files.oaiusercontent.com/down")
    assert exc.value.status_code == 502
    assert exc.value.data["error_kind"] == "upstream_unavailable"


def test_sanitize_upload_filename():
    assert sanitize_upload_filename("../../etc/passwd") == "passwd"
    assert sanitize_upload_filename("..\\..\\evil.png") == "evil.png"
    assert sanitize_upload_filename('bad\r\n"name.png') == "badname.png"
    assert sanitize_upload_filename("") == "arquivo"
    assert sanitize_upload_filename("...") == "arquivo"
