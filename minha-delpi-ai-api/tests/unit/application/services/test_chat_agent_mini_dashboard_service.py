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


def test_build_dashboard_includes_user_ranking_table():
    stats = {
        "windowHours": 168,
        "sessionsInWindow": 3,
        "messagesInWindow": 24,
        "totalSessions": 10,
        "actionProvidersCount": 2,
        "sharesCount": 1,
        "userRanking": [
            {
                "userId": "11111111-1111-4111-8111-111111111111",
                "messages": 40,
                "sessions": 2,
                "userName": "Maria",
                "userEmail": "maria@delpi.com",
            },
            {
                "userId": "22222222-2222-4222-8222-222222222222",
                "messages": 12,
                "sessions": 1,
                "userName": "João",
            },
        ],
    }

    dashboard = ChatAgentMiniDashboardService.build_dashboard(stats)

    assert len(dashboard["panels"]) == 3
    ranking_panel = dashboard["panels"][2]
    assert ranking_panel["id"] == "user-ranking"
    assert ranking_panel["presentation"]["type"] == "table"
    assert ranking_panel["presentation"]["rows"][0]["user"] == "Maria (maria@delpi.com)"
    assert ranking_panel["presentation"]["rows"][0]["messages"] == 40
    assert ranking_panel["presentation"]["rows"][1]["rank"] == 2


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
