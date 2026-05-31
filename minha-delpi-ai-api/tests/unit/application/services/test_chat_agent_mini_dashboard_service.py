from app.application.services.chat_agent_mini_dashboard_service import (
    ChatAgentMiniDashboardService,
)


def test_build_dashboard_has_kpi_and_chart_panels():
    stats = {
        "windowHours": 168,
        "sessionsInWindow": 3,
        "messagesInWindow": 24,
        "totalSessions": 10,
        "actionProvidersCount": 2,
        "sharesCount": 1,
    }

    dashboard = ChatAgentMiniDashboardService.build_dashboard(stats)

    assert dashboard["type"] == "dashboard"
    assert len(dashboard["panels"]) == 2
    assert dashboard["panels"][0]["presentation"]["type"] == "kpi"
    assert dashboard["panels"][1]["presentation"]["type"] == "chart"


def test_recommendations_when_no_sessions():
    stats = {
        "sessionsInWindow": 0,
        "messagesInWindow": 0,
        "actionProvidersCount": 0,
    }

    items = ChatAgentMiniDashboardService.build_recommendations(stats)

    assert any("Simulação" in line for line in items)


def test_recommendations_specialization_disabled():
    stats = {
        "sessionsInWindow": 2,
        "messagesInWindow": 4,
        "actionProvidersCount": 1,
    }

    items = ChatAgentMiniDashboardService.build_recommendations(
        stats,
        specialization={"enabled": False, "allowedTools": []},
    )

    assert any("Especialização desligada" in line for line in items)
