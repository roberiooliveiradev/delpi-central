from app.application.services.chat_web_search_research_activity_service import (
    ChatWebSearchResearchActivityService,
)


def test_build_research_activity_with_attempted_queries_and_sites():
    tool_context = {
        "webSearchPayload": {
            "query": "tyco",
            "retriedQuery": "Tyco International",
            "attemptedQueries": ["tyco", "Tyco International"],
            "searchStatus": "success",
            "provider": "tavily",
            "results": [
                {
                    "title": "Tyco International - Wikipedia",
                    "url": "https://en.wikipedia.org/wiki/Tyco_International",
                    "snippet": "Empresa histórica.",
                    "source": "tavily",
                },
                {
                    "title": "Tyco Electronics",
                    "url": "https://www.te.com/",
                    "snippet": "Site corporativo.",
                    "source": "tavily",
                },
            ],
        },
        "webSources": [
            {
                "title": "wikipedia.org",
                "sourceRef": "https://en.wikipedia.org/wiki/Tyco_International",
                "scope": "web_search",
            }
        ],
    }

    research = ChatWebSearchResearchActivityService.build(
        tool_context=tool_context,
        pipeline_stages=["web_search", "web_search_synthesis"],
        latency_ms=13000,
    )

    assert research is not None
    assert research["sourceCount"] >= 2
    assert research["provider"] == "tavily"
    assert research["synthesized"] is True
    assert research["attemptedQueries"] == ["tyco", "Tyco International"]
    assert len(research["steps"]) >= 3
    assert research["steps"][0]["type"] == "search"
    assert any(step["type"] == "synthesis" for step in research["steps"])
    assert any(step["type"] == "organize" for step in research["steps"])


def test_build_research_propagates_source_evaluation():
    tool_context = {
        "webSearchPayload": {
            "query": "DELPI Conexões Elétricas",
            "searchStatus": "success",
            "preferOfficial": True,
            "searchMode": "deep",
            "results": [
                {
                    "title": "Manual CFW500",
                    "url": "https://www.weg.net/manual/cfw500",
                    "snippet": "PDF",
                    "source": "tavily",
                    "sourceType": "manufacturer",
                    "qualityScore": 0.95,
                    "isOfficial": True,
                },
            ],
            "sourceEvaluation": {
                "confidence": "high",
                "sourceTypes": ["manufacturer"],
                "warnings": [],
                "excludedSources": [],
            },
        },
        "webSources": [],
    }

    research = ChatWebSearchResearchActivityService.build(
        tool_context=tool_context,
        pipeline_stages=["web_search"],
        latency_ms=5000,
    )

    assert research is not None
    assert research["confidence"] == "high"
    assert research["sourceTypes"] == ["manufacturer"]
    assert research["sites"][0]["isOfficial"] is True
    assert research["sites"][0]["sourceType"] == "manufacturer"


def test_attach_to_assistant_metadata_only_when_web_search_payload_exists():
    metadata: dict = {"sources": []}

    ChatWebSearchResearchActivityService.attach_to_assistant_metadata(
        metadata,
        tool_context={"webSources": []},
        pipeline_stages=[],
        latency_ms=1000,
    )

    assert "webSearchResearch" not in metadata

    ChatWebSearchResearchActivityService.attach_to_assistant_metadata(
        metadata,
        tool_context={
            "webSearchPayload": {
                "query": "JST-SPS-21T-250S",
                "searchStatus": "success",
                "results": [
                    {
                        "title": "DigiKey",
                        "url": "https://www.digikey.com/product-detail/en/jst/123",
                        "snippet": "Preço disponível.",
                        "source": "tavily",
                    }
                ],
            },
            "webSources": [
                {
                    "title": "digikey.com",
                    "sourceRef": "https://www.digikey.com/product-detail/en/jst/123",
                    "scope": "web_search",
                }
            ],
        },
        pipeline_stages=["web_search"],
        latency_ms=4200,
    )

    assert "webSearchResearch" in metadata
    assert metadata["webSearchResearch"]["durationMs"] == 4200
