from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.llm.http_stream_utf8 import (
    decode_stream_line,
    repair_utf8_mojibake,
)
from app.infrastructure.llm.openai_compatible_llm_gateway import OpenAiCompatibleLlmGateway


@pytest.fixture
def gateway(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("LLM_TEXT_BASE_URL", "https://api.test/v1")
    monkeypatch.setenv("LLM_TEXT_MODEL", "gpt-test")
    monkeypatch.setenv("LLM_TEXT_API_KEY", "token")
    return OpenAiCompatibleLlmGateway()


def test_repair_utf8_mojibake_from_latin1_misread():
    broken = "atÃ© vocÃª"
    assert repair_utf8_mojibake(broken) == "até você"
    assert repair_utf8_mojibake("até você") == "até você"


def test_decode_stream_line_bytes_utf8():
    raw = 'data: {"choices":[{"delta":{"content":"até"}}]}'.encode("utf-8")
    assert "até" in (decode_stream_line(raw) or "")


def test_generate_returns_content(gateway):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "choices": [{"message": {"content": " resposta "}}],
    }

    with patch(
        "app.infrastructure.llm.openai_compatible_llm_gateway.requests.post",
        return_value=response,
    ) as post:
        content = gateway.generate([{"role": "user", "content": "oi"}])

    assert content == "resposta"
    post.assert_called_once()
    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer token"
    assert response.encoding == "utf-8"


def test_generate_falls_back_to_reasoning_when_content_empty(gateway):
    """Kimi K3 / OpenRouter: content null, texto só em reasoning."""
    from app.composition.content_composer import configure_domain_infrastructure_ports

    configure_domain_infrastructure_ports()
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": None,
                    "reasoning": " Relatório do desenho 90261842: conforme. ",
                },
            }
        ],
    }

    with patch(
        "app.infrastructure.llm.openai_compatible_llm_gateway.requests.post",
        return_value=response,
    ):
        content = gateway.generate([{"role": "user", "content": "analise"}])

    assert content == "Relatório do desenho 90261842: conforme."


def test_generate_replaces_cot_reasoning_with_safe_fallback(gateway):
    from app.composition.content_composer import configure_domain_infrastructure_ports
    from app.domain.services.chat_llm_generation_context_service import (
        consume_reasoning_fallback,
    )
    from app.domain.services.chat_llm_synthesis_delivery_content_service import (
        ChatLlmSynthesisDeliveryContentService,
    )

    configure_domain_infrastructure_ports()
    consume_reasoning_fallback()
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": None,
                    "reasoning": (
                        "According to my instructions, the user's message is vague. "
                        "I should ask for clarification."
                    ),
                },
            }
        ],
    }

    with patch(
        "app.infrastructure.llm.openai_compatible_llm_gateway.requests.post",
        return_value=response,
    ):
        content = gateway.generate([{"role": "user", "content": "programação"}])

    assert content == ChatLlmSynthesisDeliveryContentService.safe_fallback_answer()
    assert "according to my instructions" not in content.lower()


def test_stream_skips_cot_reasoning_delta(gateway):
    from app.composition.content_composer import configure_domain_infrastructure_ports

    configure_domain_infrastructure_ports()
    lines = [
        b'data: {"choices":[{"delta":{"reasoning":"According to my instructions"}}]}',
        b"data: [DONE]",
    ]

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.iter_lines.return_value = iter(lines)
    response.__enter__ = MagicMock(return_value=response)
    response.__exit__ = MagicMock(return_value=False)

    with patch(
        "app.infrastructure.llm.openai_compatible_llm_gateway.requests.post",
        return_value=response,
    ):
        chunks = list(gateway.stream([{"role": "user", "content": "oi"}]))

    assert chunks == []


def test_generate_with_tools_parses_tool_calls(gateway):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "function": {
                                "name": "execute_external_action",
                                "arguments": '{"action_id":"get_product"}',
                            },
                        }
                    ],
                }
            }
        ],
    }

    with patch(
        "app.infrastructure.llm.openai_compatible_llm_gateway.requests.post",
        return_value=response,
    ):
        result = gateway.generate_with_tools(
            [{"role": "user", "content": "estoque"}],
            [{"type": "function", "function": {"name": "execute_external_action"}}],
        )

    assert result.tool_calls[0].name == "execute_external_action"
    assert result.tool_calls[0].arguments["action_id"] == "get_product"


def test_stream_yields_reasoning_when_content_delta_absent(gateway):
    lines = [
        b'data: {"choices":[{"delta":{"reasoning":"OK"}}]}',
        b"data: [DONE]",
    ]

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.iter_lines.return_value = iter(lines)
    response.__enter__ = MagicMock(return_value=response)
    response.__exit__ = MagicMock(return_value=False)

    with patch(
        "app.infrastructure.llm.openai_compatible_llm_gateway.requests.post",
        return_value=response,
    ):
        chunks = list(gateway.stream([{"role": "user", "content": "oi"}]))

    assert chunks == ["OK"]


def test_stream_yields_utf8_chunks_from_bytes(gateway):
    lines = [
        b'data: {"choices":[{"delta":{"content":"Ol"}}]}',
        'data: {"choices":[{"delta":{"content":"\u00e1"}}]}'.encode("utf-8"),
        b"data: [DONE]",
    ]

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.iter_lines.return_value = iter(lines)
    response.__enter__ = MagicMock(return_value=response)
    response.__exit__ = MagicMock(return_value=False)

    with patch(
        "app.infrastructure.llm.openai_compatible_llm_gateway.requests.post",
        return_value=response,
    ):
        chunks = list(gateway.stream([{"role": "user", "content": "oi"}]))

    assert chunks == ["Ol", "á"]
    response.iter_lines.assert_called_with(decode_unicode=False)
    assert response.encoding == "utf-8"


def test_stream_repairs_mojibake_delta(gateway):
    lines = [
        'data: {"choices":[{"delta":{"content":"atÃ©"}}]}'.encode("utf-8"),
        b"data: [DONE]",
    ]

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.iter_lines.return_value = iter(lines)
    response.__enter__ = MagicMock(return_value=response)
    response.__exit__ = MagicMock(return_value=False)

    with patch(
        "app.infrastructure.llm.openai_compatible_llm_gateway.requests.post",
        return_value=response,
    ):
        chunks = list(gateway.stream([{"role": "user", "content": "oi"}]))

    assert chunks == ["até"]
