from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.embeddings.openai_compatible_embedding_gateway import (
    OpenAiCompatibleEmbeddingGateway,
)


@pytest.fixture
def gateway(monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai_compatible")
    monkeypatch.setenv("EMBEDDING_BASE_URL", "https://api.test/v1")
    monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-3-small")
    monkeypatch.setenv("EMBEDDING_API_KEY", "token")
    return OpenAiCompatibleEmbeddingGateway()


def test_embed_returns_vector(gateway):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "data": [{"embedding": [0.1, 0.2, 0.3]}],
    }

    with patch(
        "app.infrastructure.embeddings.openai_compatible_embedding_gateway.requests.post",
        return_value=response,
    ) as post:
        vector = gateway.embed("consulta")

    assert vector == [0.1, 0.2, 0.3]
    post.assert_called_once()
    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer token"
