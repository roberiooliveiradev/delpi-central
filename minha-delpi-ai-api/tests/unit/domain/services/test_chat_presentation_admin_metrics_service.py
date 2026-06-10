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
    assert summary["switchToTableCount"] == 0
    assert summary["engagementRate"] == 2.0
    assert summary["topViewTargets"] == [{"label": "chart", "count": 1}]
    assert isinstance(summary["alerts"], list)


def test_aggregate_alerts_high_view_switch_rate():
    impressions = [
        {
            "loggedAt": "2026-06-01T12:00:00Z",
            "snapshot": {"selected": "chart", "presentationType": "chart"},
        }
        for _ in range(10)
    ]
    events = [
        {
            "loggedAt": "2026-06-01T12:01:00Z",
            "snapshot": {
                "event": "presentation_view_switch",
                "from": "chart",
                "to": "table",
            },
        }
        for _ in range(6)
    ]

    summary = ChatPresentationAdminMetricsService.aggregate(
        impression_entries=impressions,
        event_entries=events,
        hours=168,
        since_iso="2026-05-25T12:00:00Z",
    )

    assert summary["viewSwitchRate"] >= 0.45
    assert any("troca de formato" in alert.lower() for alert in summary["alerts"])
    assert any("tabela" in alert.lower() for alert in summary["alerts"])


def test_snapshot_format_respected_chart_family():
    snapshot = ChatPresentationAdminMetricsService.snapshot_from_assistant_metadata(
        {
            "toolCalls": [
                {
                    "metadata": {
                        "ok": True,
                        "preferredFormat": "chart",
                        "presentation": {"type": "chart", "chartType": "horizontal_bar"},
                        "presentationDecision": {
                            "selected": "horizontal_bar",
                            "availableViews": ["horizontal_bar", "table"],
                        },
                    }
                }
            ]
        }
    )

    assert snapshot is not None
    assert snapshot["preferredFormat"] == "chart"
    assert snapshot["formatRespected"] is True


def test_aggregate_session_format_respected_ratio():
    impressions = [
        {
            "loggedAt": "2026-06-01T12:00:00Z",
            "snapshot": {
                "selected": "table",
                "preferredFormat": "table",
                "formatRespected": True,
            },
        },
        {
            "loggedAt": "2026-06-01T12:01:00Z",
            "snapshot": {
                "selected": "chart",
                "preferredFormat": "table",
                "formatRespected": False,
            },
        },
        {
            "loggedAt": "2026-06-01T12:02:00Z",
            "snapshot": {
                "selected": "horizontal_bar",
                "presentationType": "chart",
            },
        },
    ]

    summary = ChatPresentationAdminMetricsService.aggregate(
        impression_entries=impressions,
        event_entries=[],
        hours=24,
        since_iso="2026-05-31T12:00:00Z",
    )

    assert summary["explicitPreferenceTurns"] == 2
    assert summary["formatRespectedTurns"] == 1
    assert summary["sessionFormatRespectedRatio"] == 0.5


def test_aggregate_alerts_no_impressions():
    summary = ChatPresentationAdminMetricsService.aggregate(
        impression_entries=[],
        event_entries=[],
        hours=24,
        since_iso="2026-05-31T12:00:00Z",
    )

    assert summary["alerts"]
    assert "Nenhuma resposta" in summary["alerts"][0]
