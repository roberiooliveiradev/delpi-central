from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.llm.openai_compatible_llm_gateway import OpenAiCompatibleLlmGateway


@pytest.fixture
def gateway(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("LLM_TEXT_BASE_URL", "https://api.test/v1")
    monkeypatch.setenv("LLM_TEXT_MODEL", "gpt-test")
    monkeypatch.setenv("LLM_TEXT_API_KEY", "token")
    return OpenAiCompatibleLlmGateway()


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


def test_stream_yields_chunks(gateway):
    lines = [
        'data: {"choices":[{"delta":{"content":"Ol"}}]}',
        'data: {"choices":[{"delta":{"content":"á"}}]}',
        "data: [DONE]",
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
