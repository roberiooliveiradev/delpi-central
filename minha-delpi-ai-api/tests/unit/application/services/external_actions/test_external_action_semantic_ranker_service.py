from app.application.services.external_actions.external_action_semantic_ranker_service import (
    ExternalActionSemanticRankerService,
)
from app.infrastructure.embeddings.disabled_embedding_gateway import DisabledEmbeddingGateway


class FakeEmbeddingGateway:
    def __init__(self, vectors: dict[str, list[float]]):
        self.vectors = vectors
        self.calls = 0

    def embed(self, text: str) -> list[float]:
        self.calls += 1
        return self.vectors[text]


def _action_embedding_key(method: str, path: str, summary: str) -> str:
    return " | ".join([method.upper(), path, summary])


def test_rank_orders_candidates_by_similarity():
    service = ExternalActionSemanticRankerService(
        FakeEmbeddingGateway(
            {
                "pedidos abertos": [1.0, 0.0],
                _action_embedding_key("GET", "/orders", "list open orders"): [0.95, 0.05],
                _action_embedding_key("GET", "/products", "list products"): [0.0, 1.0],
            }
        )
    )

    ranked = service.rank(
        "pedidos abertos",
        [
            {
                "actionId": "products",
                "method": "GET",
                "path": "/products",
                "summary": "list products",
            },
            {
                "actionId": "orders",
                "method": "GET",
                "path": "/orders",
                "summary": "list open orders",
            },
        ],
    )

    assert ranked
    assert ranked[0]["actionId"] == "orders"
    assert ranked[0]["selectionScore"] >= 0.42


def test_rank_returns_empty_when_below_min_score():
    service = ExternalActionSemanticRankerService(
        FakeEmbeddingGateway(
            {
                "pergunta genérica": [1.0, 0.0],
                _action_embedding_key("GET", "/unrelated", "something else"): [0.0, 1.0],
            }
        )
    )

    ranked = service.rank(
        "pergunta genérica",
        [
            {
                "actionId": "unrelated",
                "method": "GET",
                "path": "/unrelated",
                "summary": "something else",
            }
        ],
    )

    assert ranked == []


def test_rank_skips_http_when_embedding_provider_off():
    """Embed off: retorna candidatos sem chamar gateway (R8 / selectionEmbedMs ~0)."""

    class CountingDisabled(DisabledEmbeddingGateway):
        def __init__(self):
            self.calls = 0

        def embed(self, text: str) -> list[float]:
            self.calls += 1
            return super().embed(text)

    gw = CountingDisabled()
    candidates = [
        {
            "actionId": "orders",
            "method": "GET",
            "path": "/orders",
            "summary": "list open orders",
        }
    ]
    service = ExternalActionSemanticRankerService(gw)
    ranked = service.rank("pedidos abertos", candidates)
    assert ranked is candidates
    assert gw.calls == 0
