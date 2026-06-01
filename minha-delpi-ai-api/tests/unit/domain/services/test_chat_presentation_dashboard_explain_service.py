from app.domain.services.chat_presentation_dashboard_explain_service import (
    ChatPresentationDashboardExplainService,
)
from app.application.services.chat_presentation_interactivity_service import (
    ChatPresentationInteractivityService,
)


def test_build_dashboard_explanation():
    presentation = {
        "type": "dashboard",
        "title": "Painel de eficiência fabril",
        "panels": [
            {
                "id": "summary",
                "title": "Resumo",
                "presentation": {
                    "type": "kpi",
                    "title": "Resumo",
                    "cards": [{"label": "Eficiência média", "value": 85, "unit": "%"}],
                },
            },
            {
                "id": "items",
                "title": "Itens",
                "presentation": {
                    "type": "table",
                    "title": "LMPs",
                    "columns": [{"key": "nome", "label": "Operador"}],
                    "rows": [{"nome": "A"}, {"nome": "B"}],
                },
            },
        ],
    }

    text = ChatPresentationDashboardExplainService.build(
        presentation=presentation,
        decision={"insight": "Resumo do dia."},
    )

    assert "Painel de eficiência fabril" in text
    assert "2 bloco" in text
    assert "Eficiência média" in text
    assert "2 linha" in text


def test_dashboard_chip_inline_action():
    suggestions = ChatPresentationInteractivityService.build_from_tool_calls(
        [
            {
                "name": "execute_external_action",
                "metadata": {"ok": True, "presentation": {"type": "dashboard", "panels": []}},
            }
        ]
    )

    explain = next(item for item in suggestions if item["label"] == "Explique esse painel")

    assert explain.get("inlineAction") == "explain_dashboard"
