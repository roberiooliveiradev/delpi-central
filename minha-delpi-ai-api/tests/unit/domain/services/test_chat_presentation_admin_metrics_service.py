from app.domain.services.chat_presentation_admin_metrics_service import (
    ChatPresentationAdminMetricsService,
)


def test_snapshot_from_assistant_metadata():
    snapshot = ChatPresentationAdminMetricsService.snapshot_from_assistant_metadata(
        {
            "toolCalls": [
                {
                    "metadata": {
                        "ok": True,
                        "presentation": {"type": "chart", "chartType": "horizontal_bar"},
                        "presentationDecision": {
                            "selected": "horizontal_bar",
                            "availableViews": ["horizontal_bar", "table", "chart"],
                        },
                    }
                }
            ]
        }
    )

    assert snapshot is not None
    assert snapshot["selected"] == "horizontal_bar"
    assert snapshot["chartType"] == "horizontal_bar"


def test_aggregate_presentation_metrics():
    summary = ChatPresentationAdminMetricsService.aggregate(
        impression_entries=[
            {
                "loggedAt": "2026-06-01T12:00:00Z",
                "snapshot": {
                    "selected": "horizontal_bar",
                    "presentationType": "chart",
                    "chartType": "horizontal_bar",
                },
            }
        ],
        event_entries=[
            {
                "loggedAt": "2026-06-01T12:01:00Z",
                "snapshot": {
                    "event": "presentation_view_switch",
                    "from": "table",
                    "to": "chart",
                },
            },
            {
                "loggedAt": "2026-06-01T12:02:00Z",
                "snapshot": {
                    "event": "presentation_axis_change",
                    "column": "eficiencia_percentual",
                },
            },
        ],
        hours=168,
        since_iso="2026-05-25T12:00:00Z",
    )

    assert summary["responsesWithRichPresentation"] == 1
    assert summary["eventsCount"] == 2
    assert summary["viewSwitchCount"] == 1
    assert summary["axisChangeCount"] == 1
