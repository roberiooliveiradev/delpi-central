from app.domain.services.chat_web_search_admin_metrics_service import (
    ChatWebSearchAdminMetricsService,
)
from app.domain.services.chat_web_search_query_security_service import (
    ChatWebSearchQuerySecurityService,
)


def test_snapshot_from_web_search_research():
    snapshot = ChatWebSearchAdminMetricsService.snapshot_from_metadata(
        {
            "webSearchResearch": {
                "searchStatus": "success",
                "sourceCount": 3,
                "confidence": "high",
                "preferOfficial": True,
                "searchMode": "deep",
                "synthesized": True,
                "sites": [
                    {
                        "hostname": "weg.net",
                        "isOfficial": True,
                        "sourceQuality": {"type": "official_manufacturer"},
                    }
                ],
                "querySecurity": {"redacted": True},
            }
        }
    )

    assert snapshot is not None
    assert snapshot["hasOfficialSource"] is True
    assert snapshot["queryRedacted"] is True
    assert snapshot["synthesized"] is True


def test_enrich_audit_metadata():
    audit = {}
    ChatWebSearchAdminMetricsService.enrich_audit_metadata(
        audit,
        assistant_metadata={
            "webSearchResearch": {
                "searchStatus": "success",
                "sourceCount": 1,
            }
        },
    )

    assert "webSearchMetrics" in audit


def test_aggregate_alerts_on_low_official_rate():
    entries = [
        {
            "loggedAt": "2026-06-01T12:00:00+00:00",
            "snapshot": {
                "searchStatus": "success",
                "sourceCount": 2,
                "confidence": "low",
                "hasOfficialSource": False,
            },
        }
        for _ in range(6)
    ]

    summary = ChatWebSearchAdminMetricsService.aggregate(
        entries=entries,
        hours=24,
        since_iso="2026-06-01T00:00:00+00:00",
    )

    assert summary["totalSearches"] == 6
    assert summary["officialSourceRate"] == 0.0
    assert summary["alerts"]


def test_is_web_feedback_reason():
    assert ChatWebSearchAdminMetricsService.is_web_feedback_reason("web_bad_source")
    assert ChatWebSearchAdminMetricsService.is_web_feedback_reason("routing_unneeded_web")
    assert not ChatWebSearchAdminMetricsService.is_web_feedback_reason("wrong_product")


def test_build_admin_debug_web_search():
    debug = ChatWebSearchAdminMetricsService.build_admin_debug_web_search(
        tool_context={
            "webSearchPayload": {
                "provider": "searxng",
                "searchStatus": "success",
                "attemptedQueries": ["WEG CFW500 manual"],
                "sourceEvaluation": {"confidence": "high", "warnings": []},
            }
        }
    )

    assert debug is not None
    assert debug["enabled"] is True
    assert debug["queries"] == ["WEG CFW500 manual"]


def test_web_follow_up_labels_exposed_on_service_class():
    labels = ChatWebSearchAdminMetricsService.web_follow_up_labels()

    assert isinstance(labels, frozenset)


def test_security_redacted_triggers_public_query():
    result = ChatWebSearchQuerySecurityService.sanitize(
        "cliente ABC preco interno R$ 10",
        extracted_query="cliente ABC preco interno R$ 10",
    )

    assert result.redacted
    assert "informacoes publicas" in result.query
