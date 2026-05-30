from app.infrastructure.gateways.web_search_http_gateway import WebSearchHttpGateway


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_search_parses_instant_answer(monkeypatch):
    gateway = WebSearchHttpGateway()

    def fake_get(*args, **kwargs):
        return FakeResponse(
            {
                "Heading": "Python",
                "AbstractText": "Linguagem de programação.",
                "AbstractURL": "https://example.com/python",
                "RelatedTopics": [
                    {"Text": "Python software", "FirstURL": "https://example.com/2"},
                ],
            }
        )

    monkeypatch.setattr(
        "app.infrastructure.gateways.web_search_http_gateway.requests.get",
        fake_get,
    )

    payload = gateway.search("python", max_results=3)

    assert payload["query"] == "python"
    assert len(payload["results"]) >= 1
    assert payload["results"][0]["snippet"] == "Linguagem de programação."


def test_search_empty_query():
    gateway = WebSearchHttpGateway()

    payload = gateway.search("   ")

    assert payload["results"] == []
