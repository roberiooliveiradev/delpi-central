from app.infrastructure.embeddings.local_embedding_gateway import LocalEmbeddingGateway


def test_embed_many_preserves_order(monkeypatch):
    gateway = LocalEmbeddingGateway()
    calls: list[str] = []

    def fake_embed(text: str) -> list[float]:
        calls.append(text)
        return [float(len(text))]

    monkeypatch.setattr(gateway, "embed", fake_embed)

    result = gateway.embed_many(["a", "bb", "ccc"])

    assert result == [[1.0], [2.0], [3.0]]
    assert calls == ["a", "bb", "ccc"]
