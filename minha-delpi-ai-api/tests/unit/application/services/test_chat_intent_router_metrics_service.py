from app.domain.services.chat_intent_router_metrics_service import ChatIntentRouterMetricsService


def test_aggregate_snapshots_counts_intents():
    entries = [
        {
            "loggedAt": "2026-05-30T10:00:00Z",
            "action": "chat.message.sent",
            "snapshot": {
                "intent": "operational_query",
                "decision": "operational_action",
                "ambiguous": True,
            },
        },
        {
            "loggedAt": "2026-05-30T11:00:00Z",
            "action": "chat.message.streamed",
            "snapshot": {
                "intent": "text_task",
                "decision": "skip_tools",
                "requiresWeb": False,
            },
        },
        {
            "loggedAt": "2026-05-30T12:00:00Z",
            "action": "chat.message.sent",
            "snapshot": {
                "intent": "mixed_task",
                "decision": "mixed_decompose",
            },
        },
    ]

    result = ChatIntentRouterMetricsService.aggregate_snapshots(
        entries,
        hours=168,
        since_iso="2026-05-23T00:00:00Z",
    )

    assert result["routesCount"] == 3
    assert result["ambiguousCount"] == 1
    assert result["mixedTaskCount"] == 1
    assert result["textSkipToolsCount"] == 1
    assert result["byIntent"]["operational_query"] == 1


def test_enrich_audit_metadata():
    audit = {}

    ChatIntentRouterMetricsService.enrich_audit_metadata(
        audit,
        route={
            "intent": "web_search",
            "confidence": 0.9,
            "router": {"decision": "web_search", "reason": "explicit_web_request"},
        },
    )

    assert audit["intentRouting"]["intent"] == "web_search"
    assert audit["intentRouting"]["decision"] == "web_search"
