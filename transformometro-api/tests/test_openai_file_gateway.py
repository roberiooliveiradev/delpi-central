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


# --------------------------------------------------------------------------
# R4.2-C1 — observed fileParams delivery host via env allowlist
# --------------------------------------------------------------------------

_OBSERVED_HOST = "oaisdmntprbrazilsouth.blob.core.windows.net"


def test_env_override_parses_csv_hosts(monkeypatch):
    monkeypatch.setenv(
        "OPENAI_FILE_DOWNLOAD_HOSTS",
        f" files.oaiusercontent.com , {_OBSERVED_HOST.upper()} ,, ",
    )
    hosts = mod._allowed_hosts()
    assert hosts == ("files.oaiusercontent.com", _OBSERVED_HOST)
    # Empty segments never become a wildcard entry.
    assert "" not in hosts


def test_observed_fileparams_host_allowed_when_configured(monkeypatch):
    monkeypatch.setenv(
        "OPENAI_FILE_DOWNLOAD_HOSTS",
        f"files.oaiusercontent.com,{_OBSERVED_HOST}",
    )
    assert mod._host_allowed(_OBSERVED_HOST) is True
    assert mod._host_allowed("files.oaiusercontent.com") is True


def test_observed_host_denied_without_config(monkeypatch):
    monkeypatch.delenv("OPENAI_FILE_DOWNLOAD_HOSTS", raising=False)
    # Only the default OpenAI host survives — a configured deployment is
    # what unlocks the observed delivery account, never a wildcard.
    assert mod._host_allowed(_OBSERVED_HOST) is False


def test_random_azure_blob_host_denied(monkeypatch):
    monkeypatch.setenv(
        "OPENAI_FILE_DOWNLOAD_HOSTS",
        f"files.oaiusercontent.com,{_OBSERVED_HOST}",
    )
    for host in (
        "evilcorp.blob.core.windows.net",
        "blob.core.windows.net",
        "example.com",
        # Suffix confusion: attacker-owned account sharing the string.
        f"attacker-{_OBSERVED_HOST}",
        # Subdomain trick: observed host as a label under attacker zone.
        f"{_OBSERVED_HOST}.attacker.example",
    ):
        assert mod._host_allowed(host) is False, host


def test_generic_azure_wildcard_not_present():
    # The default allowlist must never resolve arbitrary Azure storage.
    assert "blob.core.windows.net" not in mod._allowed_hosts()
    assert "*.blob.core.windows.net" not in mod._allowed_hosts()


def test_regional_oaiusercontent_hosts_allowed_by_default_suffix(monkeypatch):
    """R4.4 — fileParams download URLs are served from region-sharded
    oaiusercontent.com subdomains (observed: sdmntpr*). The shared suffix
    must be allowed while lookalike hosts still fail closed."""
    monkeypatch.delenv("OPENAI_FILE_DOWNLOAD_HOSTS", raising=False)
    from tm_app.infrastructure.gateways.openai_file_gateway import (
        _host_allowed,
    )

    assert _host_allowed("sdmntprbrazilsouth.oaiusercontent.com")
    assert _host_allowed("sdmntprcentralus.oaiusercontent.com")
    assert _host_allowed("files.oaiusercontent.com")
    # Suffix-confusion and foreign hosts still denied.
    assert not _host_allowed("oaiusercontent.com.evil.example")
    assert not _host_allowed("evil-oaiusercontent.com")
    assert not _host_allowed("example.com")


# --------------------------------------------------------------------------
# Sandbox / workspace path classification (remote MCP cannot read FS)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ref",
    (
        "/workspace/user_files/01-image.png",
        "/workspace/output/slide-gr-jaragua-corrigido.png",
        "/mnt/data/shot.png",
        "file:///workspace/user_files/01-image.png",
        "file:///mnt/data/shot.png",
        # Model-mangled HTTPS forms observed when agents invent URLs
        # from sandbox paths (empty host → previously FILE_URL_NOT_ALLOWED).
        "https:///workspace/user_files/01-image.png",
        "https://workspace/user_files/01-image.png",
        "https://localhost/workspace/user_files/01-image.png",
        "https://127.0.0.1/mnt/data/shot.png",
    ),
)
def test_sandbox_refs_classified(ref):
    assert mod.is_sandbox_file_reference(ref) is True


@pytest.mark.parametrize(
    "ref",
    (
        "https://files.oaiusercontent.com/file-1?sig=x",
        "https://sdmntprbrazilsouth.oaiusercontent.com/a",
        "https://evil.example.com/file",
        "",
        "file_abc123",
        "libfile_xyz",
    ),
)
def test_non_sandbox_refs_not_classified_as_sandbox(ref):
    assert mod.is_sandbox_file_reference(ref) is False


@pytest.mark.parametrize(
    "ref",
    (
        "/workspace/user_files/01-image.png",
        "/workspace/output/slide.png",
        "file:///workspace/user_files/01-image.png",
        "https:///workspace/user_files/01-image.png",
        "https://workspace/user_files/01-image.png",
    ),
)
def test_sandbox_fetch_returns_typed_path_error(ref):
    with pytest.raises(GptActionsError) as exc:
        _fetch(ref)
    assert exc.value.status_code == 400
    assert exc.value.data["error_code"] == "FILE_PATH_NOT_SUPPORTED"
    # Must not be misclassified as an allowlist/SSRF rejection.
    assert exc.value.data["error_code"] != "FILE_URL_NOT_ALLOWED"


def test_sandbox_fetch_never_opens_http_client(monkeypatch):
    """Fail closed before any network — no Client construction."""

    def _boom(**_kwargs):
        raise AssertionError("httpx.Client must not be constructed")

    monkeypatch.setattr(mod.httpx, "Client", _boom)
    with pytest.raises(GptActionsError) as exc:
        _fetch("/workspace/user_files/x.png")
    assert exc.value.data["error_code"] == "FILE_PATH_NOT_SUPPORTED"


def test_allowlisted_https_still_fetches(_client):
    """Positive sibling — host-hydrated fileParams download_url still works."""
    _client(
        _StreamResponse(
            200,
            b"\x89PNG",
            {"content-type": "image/png"},
        )
    )
    out = _fetch("https://files.oaiusercontent.com/file-ok?sig=abc")
    assert out["content"] == b"\x89PNG"
    assert out["mime"] == "image/png"
