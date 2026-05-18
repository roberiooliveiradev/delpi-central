from app.application.services.external_actions.external_action_semantic_ranker_service import (
    ExternalActionSemanticRankerService,
)


class FakeEmbeddingGateway:
    def __init__(self, vectors: dict[str, list[float]]):
        self.vectors = vectors

    def embed(self, text: str) -> list[float]:
        return self.vectors[text]


def test_rank_orders_candidates_by_similarity():
    service = ExternalActionSemanticRankerService(
        FakeEmbeddingGateway(
            {
                "pedidos abertos": [1.0, 0.0],
                "GET /orders | list open orders": [0.95, 0.05],
                "GET /products | list products": [0.0, 1.0],
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
                "GET /unrelated | something else": [0.0, 1.0],
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
