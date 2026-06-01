from app.domain.services.chat_interactivity_admin_metrics_service import (
    ChatInteractivityAdminMetricsService,
)


def test_snapshot_from_metadata():
    snapshot = ChatInteractivityAdminMetricsService.snapshot_from_metadata(
        {
            "interactivity": {
                "consolidated": True,
                "suggestions": [{"label": "Ver estoque", "query": "x"}],
                "moreSuggestions": {"consultar": [{"label": "Ver vendas", "query": "y"}]},
                "suggestionsShown": ["Ver estoque", "Ver vendas"],
                "sourceIntent": "product_lookup",
            },
        },
    )

    assert snapshot["primaryCount"] == 1
    assert snapshot["overflowCount"] == 1
    assert snapshot["hasMoreOptions"] is True


def test_aggregate_ctr():
    summary = ChatInteractivityAdminMetricsService.aggregate(
        impression_entries=[
            {
                "loggedAt": "2026-01-01T00:00:00Z",
                "snapshot": {
                    "shownCount": 2,
                    "shownLabels": ["Ver estoque", "Ver estoque"],
                    "hasMoreOptions": False,
                    "sourceIntent": "product_lookup",
                },
            },
        ],
        click_entries=[
            {
                "loggedAt": "2026-01-01T01:00:00Z",
                "snapshot": {"label": "Ver estoque", "group": "consultar"},
            },
        ],
        hours=24,
        since_iso="2026-01-01T00:00:00Z",
    )

    assert summary["responsesWithChips"] == 1
    assert summary["clicksCount"] == 1
    assert summary["clickThroughRate"] == 0.5
    assert summary["ctrByLabel"]["Ver estoque"] == 0.5
