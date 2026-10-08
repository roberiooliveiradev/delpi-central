"""C3-INTERACTION-RUNTIME-01R2 — real OpenAI-compatible provider adapter tests.

HTTP is mocked; no real provider call. Covers composition config gate,
request mapping, response mapping, failure mapping, and secret hygiene.
"""

from __future__ import annotations

import json

import pytest
import requests

from app.application.interaction.handle_interactive_turn import (
    HandleInteractiveConversationTurn,
)
from app.application.model_invocation.contracts import ModelInvocationRequest
from app.application.model_invocation.errors import (
    INVALID_STRUCTURED_OUTPUT,
    PROVIDER_REJECTED,
    PROVIDER_UNAVAILABLE,
    TIMEOUT,
    UNSUPPORTED_MODEL,
    ModelInvocationError,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.create_app import create_app
from app.domain.evidence.model import ModelRef
from app.domain.model_invocation.model import (
    GenerationConfig,
    InstructionLineage,
    InvocationFinishStatus,
    ModelInvocationId,
    ProviderExposureClass,
)
from app.infrastructure.model_invocation.openai_compatible_adapter import (
    OpenAICompatibleModelInvocationAdapter,
)


KEY = "test-secret-key-value"  # noqa: S105 - fixture value, not a real secret
BASE_URL = "https://provider.example/api/v1"
MODEL = "vendor/model-x"


def _adapter(**overrides) -> OpenAICompatibleModelInvocationAdapter:
    params = {
        "base_url": BASE_URL,
        "api_key": KEY,
        "model": MODEL,
        "timeout_seconds": 30.0,
    }
    params.update(overrides)
    return OpenAICompatibleModelInvocationAdapter(**params)


def _request(**overrides) -> ModelInvocationRequest:
    params = {
        "invocation_id": ModelInvocationId("inv-1"),
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


class _Response:
    def __init__(self, status_code: int = 200, body=None, json_error=None):
        self.status_code = status_code
        self._body = body
        self._json_error = json_error

    def json(self):
        if self._json_error is not None:
            raise self._json_error
        return self._body


def _ok_body(content, usage=None):
    return {
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "usage": usage,
    }


def _wired_port(app):
    handler = app.config.get("INTERACTION_TURN_HANDLER")
    if handler is None:
        return None
    return handler._invoke_model._port  # noqa: SLF001 - wiring assertion


# --- A. Adapter classification ---------------------------------------------


def test_adapter_is_external_approved_openai_compatible():
    adapter = _adapter()
    assert adapter.adapter_kind == "OPENAI_COMPATIBLE"
    assert adapter.exposure_class is ProviderExposureClass.EXTERNAL_APPROVED


def test_adapter_fails_closed_on_incomplete_config():
    with pytest.raises(ValueError):
        _adapter(api_key=" ")
    with pytest.raises(ValueError):
        _adapter(base_url="")
    with pytest.raises(ValueError):
        _adapter(model="")
    with pytest.raises(ValueError):
        _adapter(timeout_seconds=0)


# --- B. Request mapping -----------------------------------------------------


def test_posts_to_chat_completions_with_bearer_and_model():
    calls = []

    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return _Response(200, _ok_body('{"answer": "ok"}'))

    adapter = _adapter(http_post=fake_post)
    InvokeModel(adapter).execute(_request())

    call = calls[0]
    assert call["url"] == f"{BASE_URL}/chat/completions"
    assert call["headers"]["Authorization"] == f"Bearer {KEY}"
    assert call["json"]["model"] == MODEL
    # (connect, read) — connect is bounded by the whole invocation
    # budget; the per-recv read slice is capped at _READ_SLICE_SECONDS
    # while the chunked drain enforces the total deadline.
    assert call["timeout"] == (25.0, 0.5)


def test_messages_carry_instruction_and_user_input_and_no_tools():
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        captured["json"] = json
        return _Response(200, _ok_body('{"answer": "ok"}'))

    adapter = _adapter(http_post=fake_post)
    InvokeModel(adapter).execute(_request(input_text="pergunta do usuário"))

    body = captured["json"]
    assert "tools" not in body and "functions" not in body
    assert body["messages"][0]["role"] == "system"
    assert body["messages"][0]["content"] == "You are DÉLIA."
    assert body["messages"][-1] == {
        "role": "user",
        "content": "pergunta do usuário",
    }


def test_timeout_is_bounded_by_adapter_config():
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        captured["timeout"] = timeout
        return _Response(200, _ok_body('{"answer": "ok"}'))

    adapter = _adapter(http_post=fake_post, timeout_seconds=5.0)
    InvokeModel(adapter).execute(_request(timeout_seconds=25.0))
    assert captured["timeout"] == (5.0, 0.5)


def test_max_tokens_omitted_without_configured_default():
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        captured["json"] = json
        return _Response(200, _ok_body('{"answer": "ok"}'))

    adapter = _adapter(http_post=fake_post)
    InvokeModel(adapter).execute(_request())
    assert "max_tokens" not in captured["json"]


def test_default_max_output_units_sets_max_tokens():
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        captured["json"] = json
        return _Response(200, _ok_body('{"answer": "ok"}'))

    adapter = _adapter(http_post=fake_post, default_max_output_units=2048)
    InvokeModel(adapter).execute(_request())
    assert captured["json"]["max_tokens"] == 2048


def test_request_max_output_units_overrides_adapter_default():
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        captured["json"] = json
        return _Response(200, _ok_body('{"answer": "ok"}'))

    adapter = _adapter(http_post=fake_post, default_max_output_units=2048)
    InvokeModel(adapter).execute(
        _request(
            generation_config=GenerationConfig(max_output_units=512)
        )
    )
    assert captured["json"]["max_tokens"] == 512


# --- C. Response mapping ----------------------------------------------------


def test_valid_json_output_maps_to_payload_with_usage():
    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        return _Response(
            200,
            _ok_body(
                '{"answer": "resposta", "limitations": ["sem dados de negócio"]}',
                usage={"prompt_tokens": 10, "completion_tokens": 4},
            ),
        )

    result = InvokeModel(_adapter(http_post=fake_post)).execute(_request())
    assert result.structured_output["answer"] == "resposta"
    assert result.structured_output["limitations"] == ["sem dados de negócio"]
    assert result.finish_status is InvocationFinishStatus.COMPLETED
    assert result.usage.input_units == 10
    assert result.usage.output_units == 4
    assert result.epistemic_class.value == "HYPOTHESIS"


def test_fenced_json_output_is_accepted():
    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        return _Response(200, _ok_body('```json\n{"answer": "ok"}\n```'))

    result = InvokeModel(_adapter(http_post=fake_post)).execute(_request())
    assert result.structured_output["answer"] == "ok"


def test_non_json_output_maps_invalid_structured_output():
    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        return _Response(200, _ok_body("plain text, no json"))

    with pytest.raises(ModelInvocationError) as exc:
        InvokeModel(_adapter(http_post=fake_post)).execute(_request())
    assert exc.value.code == INVALID_STRUCTURED_OUTPUT


def test_malformed_provider_response_maps_invalid():
    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        return _Response(200, {"unexpected": True})

    with pytest.raises(ModelInvocationError) as exc:
        InvokeModel(_adapter(http_post=fake_post)).execute(_request())
    assert exc.value.code == INVALID_STRUCTURED_OUTPUT


class _GzipRaw:
    """urllib3-shaped raw stream: read1 honours ``decode_content``."""

    def __init__(self, payload: bytes):
        import gzip
        import io

        self.decode_content = False
        self._wire = io.BytesIO(gzip.compress(payload))
        self._decoded = io.BytesIO(payload)

    def read1(self, n: int = -1) -> bytes:
        return (self._decoded if self.decode_content else self._wire).read(n)


def test_gzip_encoded_provider_body_is_decoded():
    """R2B regression: a gzip provider response must parse as JSON —
    a bare ``read1()`` returns wire bytes and used to surface as
    INVALID_STRUCTURED_OUTPUT on every live model call."""
    payload = json.dumps(
        _ok_body('{"answer": "ok"}')
    ).encode()

    class _GzipResponse(_Response):
        def __init__(self):
            super().__init__(200, None)
            self.raw = _GzipRaw(payload)

    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        return _GzipResponse()

    result = InvokeModel(_adapter(http_post=fake_post)).execute(_request())
    assert result.structured_output["answer"] == "ok"


def test_tool_call_in_provider_message_is_rejected():
    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        return _Response(
            200,
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": '{"answer": "x"}',
                            "tool_calls": [{"function": {"name": "create_order"}}],
                        }
                    }
                ]
            },
        )

    with pytest.raises(ModelInvocationError) as exc:
        InvokeModel(_adapter(http_post=fake_post)).execute(_request())
    assert exc.value.code == INVALID_STRUCTURED_OUTPUT
    assert "tool" in exc.value.message.lower()


def test_tool_like_output_inside_structured_json_is_rejected():
    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        return _Response(
            200, _ok_body('{"answer": "x", "tool_calls": [{"name": "act"}]}')
        )

    with pytest.raises(ModelInvocationError) as exc:
        InvokeModel(_adapter(http_post=fake_post)).execute(_request())
    assert exc.value.code == INVALID_STRUCTURED_OUTPUT


# --- D. Failure mapping ------------------------------------------------------


def test_http_401_and_403_map_provider_rejected():
    for status in (401, 403):
        def fake_post(url, headers=None, json=None, timeout=None, stream=None, s=status):
            return _Response(s, {"error": "denied"})

        with pytest.raises(ModelInvocationError) as exc:
            InvokeModel(_adapter(http_post=fake_post)).execute(_request())
        assert exc.value.code == PROVIDER_REJECTED
        assert KEY not in str(exc.value)


def test_http_404_maps_unsupported_model():
    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        return _Response(404, {"error": "model not found"})

    with pytest.raises(ModelInvocationError) as exc:
        InvokeModel(_adapter(http_post=fake_post)).execute(_request())
    assert exc.value.code == UNSUPPORTED_MODEL


def test_http_5xx_and_429_map_provider_unavailable():
    for status in (429, 500, 503):
        def fake_post(url, headers=None, json=None, timeout=None, stream=None, s=status):
            return _Response(s, {})

        with pytest.raises(ModelInvocationError) as exc:
            InvokeModel(_adapter(http_post=fake_post)).execute(_request())
        assert exc.value.code == PROVIDER_UNAVAILABLE


def test_timeout_maps_timeout():
    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        raise requests.exceptions.Timeout("slow")

    with pytest.raises(ModelInvocationError) as exc:
        InvokeModel(_adapter(http_post=fake_post)).execute(_request())
    assert exc.value.code == TIMEOUT


def test_connection_error_maps_provider_unavailable():
    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        raise requests.exceptions.ConnectionError("dns failed")

    with pytest.raises(ModelInvocationError) as exc:
        InvokeModel(_adapter(http_post=fake_post)).execute(_request())
    assert exc.value.code == PROVIDER_UNAVAILABLE


def test_secret_never_leaks_into_errors():
    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        return _Response(401, {"error": f"invalid key {KEY}"})

    with pytest.raises(ModelInvocationError) as exc:
        InvokeModel(_adapter(http_post=fake_post)).execute(_request())
    assert KEY not in exc.value.message
    assert "Bearer" not in exc.value.message


# --- E. Composition config gate ---------------------------------------------


_LLM_ENV = {
    "DELIA_LLM_PROVIDER": "openai_compatible",
    "DELIA_LLM_BASE_URL": BASE_URL,
    "DELIA_LLM_MODEL": MODEL,
    "DELIA_LLM_API_KEY": KEY,
}


def _clean_llm_env(monkeypatch):
    for name in (
        "DELIA_LLM_PROVIDER",
        "DELIA_LLM_BASE_URL",
        "DELIA_LLM_MODEL",
        "DELIA_LLM_API_KEY",
        "DELIA_LLM_TIMEOUT_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)


def test_complete_config_wires_real_adapter(monkeypatch):
    _clean_llm_env(monkeypatch)
    for name, value in _LLM_ENV.items():
        monkeypatch.setenv(name, value)
    app = create_app(testing=False)
    assert isinstance(_wired_port(app), OpenAICompatibleModelInvocationAdapter)


@pytest.mark.parametrize(
    "missing",
    ["DELIA_LLM_BASE_URL", "DELIA_LLM_MODEL", "DELIA_LLM_API_KEY"],
)
def test_incomplete_config_fails_closed(monkeypatch, missing):
    _clean_llm_env(monkeypatch)
    for name, value in _LLM_ENV.items():
        if name != missing:
            monkeypatch.setenv(name, value)
    app = create_app(testing=False)
    assert app.config.get("INTERACTION_TURN_HANDLER") is None


def test_unsupported_provider_value_fails_closed(monkeypatch):
    _clean_llm_env(monkeypatch)
    for name, value in {**_LLM_ENV, "DELIA_LLM_PROVIDER": "anthropic"}.items():
        monkeypatch.setenv(name, value)
    app = create_app(testing=False)
    assert app.config.get("INTERACTION_TURN_HANDLER") is None


def test_testing_true_still_uses_deterministic_adapter(monkeypatch):
    _clean_llm_env(monkeypatch)
    for name, value in _LLM_ENV.items():
        monkeypatch.setenv(name, value)
    app = create_app(testing=True)
    from app.infrastructure.model_invocation.deterministic_test_adapter import (
        DeterministicTestAdapter,
    )

    assert isinstance(_wired_port(app), DeterministicTestAdapter)


def test_explicit_port_injection_beats_real_config(monkeypatch):
    _clean_llm_env(monkeypatch)
    for name, value in _LLM_ENV.items():
        monkeypatch.setenv(name, value)
    sentinel = _adapter(http_post=lambda *a, **k: None)
    app = create_app(testing=False, model_invocation_port=sentinel)
    assert _wired_port(app) is sentinel


def test_explicit_handler_injection_beats_real_config(monkeypatch):
    _clean_llm_env(monkeypatch)
    for name, value in _LLM_ENV.items():
        monkeypatch.setenv(name, value)
    sentinel = HandleInteractiveConversationTurn(
        InvokeModel(_adapter(http_post=lambda *a, **k: None))
    )
    app = create_app(testing=False, interaction_turn_handler=sentinel)
    assert app.config.get("INTERACTION_TURN_HANDLER") is sentinel


def test_real_wiring_uses_configured_model_ref(monkeypatch):
    _clean_llm_env(monkeypatch)
    for name, value in _LLM_ENV.items():
        monkeypatch.setenv(name, value)
    app = create_app(testing=False)
    handler = app.config["INTERACTION_TURN_HANDLER"]
    assert handler._model_ref.model_id == MODEL  # noqa: SLF001
    assert handler._model_ref.provider_ref == "openai_compatible"  # noqa: SLF001
