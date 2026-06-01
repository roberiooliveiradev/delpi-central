from app.domain.services.chat_presentation_chart_explain_service import (
    ChatPresentationChartExplainService,
)
from app.application.services.chat_presentation_interactivity_service import (
    ChatPresentationInteractivityService,
)
from app.application.services.chat_interactivity_suggestion_service import (
    ChatInteractivitySuggestionService,
)


def _efficiency_chart_presentation():
    return {
        "type": "chart",
        "chartType": "horizontal_bar",
        "data": [
            {
                "nome_operador": "ELISANGELA",
                "qtd_apontada": 1.8,
                "eficiencia_percentual": 147.87,
            },
            {
                "nome_operador": "SAULO",
                "qtd_apontada": 6,
                "eficiencia_percentual": 54.45,
            },
            {
                "nome_operador": "VICTOR",
                "qtd_apontada": 0.15,
                "eficiencia_percentual": 292.29,
            },
        ],
        "config": {
            "xAxis": "nome_operador",
            "yAxis": ["eficiencia_percentual"],
        },
    }


def test_build_chart_explanation_for_efficiency_horizontal_bar():
    text = ChatPresentationChartExplainService.build(
        presentation=_efficiency_chart_presentation(),
        decision={
            "selected": "horizontal_bar",
            "reason": "muitas categorias — ranking em barra horizontal",
            "insight": "Os destaques concentram-se em ELISANGELA.",
        },
    )

    assert "barras horizontais" in text.lower()
    assert "eficiencia" in text.lower() or "Eficiência" in text
    assert "100%" in text or "100 %" in text
    assert "seletores" in text.lower()


def test_presentation_chip_explain_has_inline_action():
    suggestions = ChatPresentationInteractivityService.build_from_tool_calls(
        [
            {
                "name": "execute_external_action",
                "metadata": {"ok": True, "presentation": {"type": "chart"}},
            }
        ]
    )

    explain = next(item for item in suggestions if item["label"] == "Explique esse gráfico")

    assert explain.get("inlineAction") == "explain_chart"


def test_interactivity_enrich_preserves_inline_action():
    enriched = ChatInteractivitySuggestionService._enrich(
        {
            "label": "Explique esse gráfico",
            "query": "explique o gráfico",
            "inlineAction": "explain_chart",
        },
        metadata={},
        workspace_context={},
    )

    assert enriched.get("inlineAction") == "explain_chart"
