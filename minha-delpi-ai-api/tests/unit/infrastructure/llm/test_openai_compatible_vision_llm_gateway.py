from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.llm.openai_compatible_vision_llm_gateway import (
    OpenAiCompatibleVisionLlmGateway,
)


@pytest.fixture
def gateway(monkeypatch):
    monkeypatch.setenv("VISION_LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("VISION_LLM_BASE_URL", "https://api.test/v1")
    monkeypatch.setenv("VISION_LLM_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("VISION_LLM_API_KEY", "token")
    return OpenAiCompatibleVisionLlmGateway()


def test_describe_returns_content(gateway):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "choices": [{"message": {"content": " texto extraído "}}],
    }

    with patch(
        "app.infrastructure.llm.openai_compatible_vision_llm_gateway.requests.post",
        return_value=response,
    ):
        content = gateway.describe(
            prompt="extraia o texto",
            images_b64=["abc123"],
            max_tokens=512,
        )

    assert content == "texto extraído"
