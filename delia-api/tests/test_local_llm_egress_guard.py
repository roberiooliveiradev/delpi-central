"""C3-OLLAMA-ONLY-LOCAL-LLM-TESTING-01 — fail-closed local LLM guard.

Policy: outside production the only real model endpoint allowed is the
local Ollama runtime. External paid LLM endpoints are prohibited in
local/dev/testing contexts — configuration is refused at composition
and any direct socket egress is blocked by the test conftest.

Scenarios required by the task:
  external provider in local profile / ollama unavailable /
  model not installed / invalid endpoint / schema-incompatible
  response / external fallback attempt / missing configuration.
"""

import socket

import pytest
import requests

from app.application.model_invocation.contracts import ModelInvocationRequest
from app.application.model_invocation.errors import (
    INVALID_STRUCTURED_OUTPUT,
    PROVIDER_UNAVAILABLE,
    UNSUPPORTED_MODEL,
    ModelInvocationError,
)
from app.create_app import create_app
from app.domain.evidence.model import ModelRef
from app.domain.model_invocation.model import (
    InstructionLineage,
    ModelInvocationId,
)
from app.infrastructure.config.settings import (
    Settings,
    is_local_llm_host,
    llm_egress_blocked_reason,
)
from app.infrastructure.model_invocation.openai_compatible_adapter import (
    OpenAICompatibleModelInvocationAdapter,
)

OLLAMA_URL = "http://ollama:11434/v1"
EXTERNAL_URL = "https://provider.example/api/v1"
KEY = "test-secret-key-value"  # noqa: S105 - fixture value, not a real secret
MODEL = "qwen2.5:3b"


def _env(monkeypatch, base_url, environment="development"):
    monkeypatch.setenv("DELIA_ENV", environment)
    monkeypatch.setenv("DELIA_LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("DELIA_LLM_BASE_URL", base_url)
    monkeypatch.setenv("DELIA_LLM_MODEL", MODEL)
    monkeypatch.setenv("DELIA_LLM_API_KEY", KEY)


def _request(**overrides) -> ModelInvocationRequest:
    params = {
        "invocation_id": ModelInvocationId("inv-guard-1"),
        "model_ref": ModelRef(
            model_id=MODEL,
            version="configured",
            owner_ref="DELPI",
            provider_ref="openai_compatible",
        ),
        "input_text": "Olá",
        "task_purpose_id": "delia.interaction.turn",
        "output_schema_id": "delia.interaction.turn",
        "output_schema_version": "1",
        "expected_fields": ("answer",),
        "instruction_lineage": InstructionLineage(
            instruction_id="delia.interaction.base",
            version="1",
            content_hash="x" * 64,
        ),
        "timeout_seconds": 25.0,
        "instruction_content": "You are DÉLIA.",
    }
    params.update(overrides)
    return ModelInvocationRequest(**params)


def _adapter(**overrides) -> OpenAICompatibleModelInvocationAdapter:
    params = {
        "base_url": OLLAMA_URL,
        "api_key": KEY,
        "model": MODEL,
        "timeout_seconds": 30.0,
    }
    params.update(overrides)
    return OpenAICompatibleModelInvocationAdapter(**params)


class _Response:
    def __init__(self, status_code: int = 200, body=None, json_error=None):
        self.status_code = status_code
        self._body = body
        self._json_error = json_error

    def json(self):
        if self._json_error is not None:
            raise self._json_error
        return self._body


def _handler(app):
    return app.config.get("INTERACTION_TURN_HANDLER")


# --- Host classification --------------------------------------------------


@pytest.mark.parametrize(
    "host",
    [
        "localhost",
        "127.0.0.1",
        "::1",
        "ollama",
        "host.docker.internal",
        "host.containers.internal",
        "10.0.0.5",
        "172.18.0.4",
        "192.168.15.10",
        "delia-api",
        "searxng",
    ],
)
def test_local_hosts_allowed(host):
    assert is_local_llm_host(host) is True


@pytest.mark.parametrize(
    "host",
    [
        "api.openai.com",
        "openrouter.ai",
        "8.8.8.8",
        "evil.example.org",
        "",
    ],
)
def test_external_hosts_refused(host):
    assert is_local_llm_host(host) is False


# --- Scenario 1: external provider configured in the local profile --------


def test_external_provider_blocked_in_development(monkeypatch):
    _env(monkeypatch, EXTERNAL_URL)
    settings = Settings()
    assert settings.llm_egress_blocked_reason is not None
    assert "provider.example" in settings.llm_egress_blocked_reason


def test_external_provider_blocked_in_testing(monkeypatch):
    _env(monkeypatch, EXTERNAL_URL, environment="testing")
    assert Settings().llm_egress_blocked_reason is not None


def test_external_provider_refuses_to_wire_handler(monkeypatch):
    _env(monkeypatch, EXTERNAL_URL)
    app = create_app(testing=False)
    assert _handler(app) is None


def test_production_may_use_external_provider(monkeypatch):
    _env(monkeypatch, EXTERNAL_URL, environment="production")
    settings = Settings()
    assert settings.llm_egress_blocked_reason is None
    app = create_app(testing=False)
    assert _handler(app) is not None


def test_ollama_endpoint_allowed_in_development(monkeypatch):
    _env(monkeypatch, OLLAMA_URL)
    settings = Settings()
    assert settings.llm_egress_blocked_reason is None
    app = create_app(testing=False)
    assert _handler(app) is not None


def test_loopback_endpoint_allowed_in_development(monkeypatch):
    _env(monkeypatch, "http://127.0.0.1:11434/v1")
    assert Settings().llm_egress_blocked_reason is None


# --- Scenario 2: Ollama unavailable ---------------------------------------


def test_ollama_unavailable_maps_to_provider_unavailable():
    def _refused(*args, **kwargs):
        raise requests.exceptions.ConnectionError("connection refused")

    adapter = _adapter(http_post=_refused)
    with pytest.raises(ModelInvocationError) as exc:
        adapter.invoke(_request())
    assert exc.value.code == PROVIDER_UNAVAILABLE


# --- Scenario 3: model not installed --------------------------------------


def test_missing_model_maps_to_unsupported_model():
    adapter = _adapter(
        http_post=lambda *a, **k: _Response(status_code=404, body={})
    )
    with pytest.raises(ModelInvocationError) as exc:
        adapter.invoke(_request())
    assert exc.value.code == UNSUPPORTED_MODEL


# --- Scenario 4: invalid endpoint -----------------------------------------


def test_malformed_base_url_is_blocked_in_development():
    reason = llm_egress_blocked_reason(
        environment="development", base_url="not-a-valid-url"
    )
    assert reason is not None


def test_malformed_base_url_allowed_check_via_settings(monkeypatch):
    _env(monkeypatch, "://bad")
    assert Settings().llm_egress_blocked_reason is not None


# --- Scenario 5: response incompatible with the schema --------------------


def test_non_json_response_maps_to_invalid_structured_output():
    adapter = _adapter(
        http_post=lambda *a, **k: _Response(
            status_code=200, json_error=ValueError("no json")
        )
    )
    with pytest.raises(ModelInvocationError) as exc:
        adapter.invoke(_request())
    assert exc.value.code == INVALID_STRUCTURED_OUTPUT


def test_body_missing_required_shape_maps_to_invalid_output():
    adapter = _adapter(
        http_post=lambda *a, **k: _Response(
            status_code=200, body={"unexpected": "shape"}
        )
    )
    with pytest.raises(ModelInvocationError):
        adapter.invoke(_request())


# --- Scenario 6: attempted external fallback at the socket layer ----------


def test_socket_guard_blocks_public_ip_connect():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(RuntimeError, match="external network egress"):
            sock.connect(("8.8.8.8", 443))
    finally:
        sock.close()


def test_socket_guard_blocks_external_hostname_connect():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(RuntimeError, match="external network egress"):
            sock.connect(("api.openai.com", 443))
    finally:
        sock.close()


def test_socket_guard_allows_local_connect():
    # Never reaches the OS: loopback is allowed through the guard. Use a
    # refused local port to prove the call passed the guard unmodified.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises((ConnectionRefusedError, OSError)) as exc:
            sock.connect(("127.0.0.1", 1))
        assert "external network egress" not in str(exc.value)
    finally:
        sock.close()


# --- Scenario 7: missing configuration ------------------------------------


def test_missing_provider_config_fails_closed(monkeypatch):
    monkeypatch.setenv("DELIA_ENV", "development")
    monkeypatch.setenv("DELIA_LLM_BASE_URL", OLLAMA_URL)
    app = create_app(testing=False)
    assert _handler(app) is None


def test_no_llm_config_at_all_fails_closed(monkeypatch):
    monkeypatch.setenv("DELIA_ENV", "development")
    app = create_app(testing=False)
    assert _handler(app) is None
