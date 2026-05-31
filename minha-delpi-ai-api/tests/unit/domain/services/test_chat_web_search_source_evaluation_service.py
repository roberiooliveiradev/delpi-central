from app.domain.services.chat_web_search_source_evaluation_service import (
    ChatWebSearchSourceEvaluationService,
)


def test_evaluate_url_manufacturer_weg():
    evaluation = ChatWebSearchSourceEvaluationService.evaluate_url(
        "https://www.weg.net/catalogo/cfw500",
        title="Manual CFW500",
    )

    assert evaluation.source_type == "manufacturer"
    assert evaluation.is_official is True
    assert evaluation.quality_score >= 0.9


def test_evaluate_url_forum_low_quality():
    evaluation = ChatWebSearchSourceEvaluationService.evaluate_url(
        "https://www.reddit.com/r/automation/comments/abc",
        title="CFW500 opinion",
    )

    assert evaluation.source_type == "forum"
    assert evaluation.is_official is False
    assert evaluation.quality_score < 0.5


def test_enrich_payload_orders_by_quality_and_adds_summary():
    payload = {
        "searchStatus": "success",
        "preferOfficial": False,
        "results": [
            {
                "title": "Reddit thread",
                "url": "https://www.reddit.com/r/plc/comments/1",
                "snippet": "opinion",
                "source": "tavily",
            },
            {
                "title": "WEG manual",
                "url": "https://www.weg.net/files/manual-cfw500.pdf",
                "snippet": "official doc",
                "source": "tavily",
            },
        ],
    }

    enriched = ChatWebSearchSourceEvaluationService.enrich_payload(payload)

    assert enriched is not None
    results = enriched["results"]
    assert results[0]["sourceType"] == "manufacturer"
    assert results[0]["isOfficial"] is True
    assert results[-1]["sourceType"] == "forum"

    summary = enriched["sourceEvaluation"]
    assert summary["confidence"] in {"high", "medium", "low"}
    assert "manufacturer" in summary["sourceTypes"]


def test_enrich_payload_excludes_low_quality_when_prefer_official():
    payload = {
        "searchStatus": "success",
        "preferOfficial": True,
        "results": [
            {
                "title": "Opinião aleatória",
                "url": "https://random-opinions.example/thread",
                "snippet": "guess",
                "source": "tavily",
            },
            {
                "title": "WEG",
                "url": "https://www.weg.net/support",
                "snippet": "support",
                "source": "tavily",
            },
        ],
    }

    enriched = ChatWebSearchSourceEvaluationService.enrich_payload(payload)

    assert enriched is not None
    assert len(enriched["results"]) == 1
    assert enriched["results"][0]["isOfficial"] is True
    assert len(enriched["sourceEvaluation"]["excludedSources"]) >= 1


def test_format_warnings_block_when_no_trusted_official():
    payload = {
        "sourceEvaluation": {
            "warnings": [
                "Não encontramos página oficial entre os resultados.",
            ],
        },
    }

    block = ChatWebSearchSourceEvaluationService.format_warnings_block(payload)

    assert block is not None
    assert "Observação sobre as fontes" in block
    assert "oficial" in block.lower()
