"""Testes — análise de resultado e visualização SQL."""

from app.domain.services.chat_sql_result_analyzer_service import ChatSqlResultAnalyzerService
from app.domain.services.chat_sql_visualization_advisor_service import (
    ChatSqlVisualizationAdvisorService,
)


def test_analyze_empty_sql_resultset():
    analysis = ChatSqlResultAnalyzerService.analyze_payload(
        {
            "total_resultsets": 1,
            "resultsets": [
                {
                    "columns": ["product_code", "total"],
                    "total": 0,
                    "data": [],
                }
            ],
        }
    )

    assert analysis is not None
    assert analysis["isEmpty"] is True
    assert analysis["rowCount"] == 0
    assert len(analysis["recoverySuggestions"]) >= 2


def test_analyze_tool_calls_from_sql_execution():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/data/sql",
                "data": {
                    "resultsets": [
                        {
                            "columns": ["cliente", "faturamento"],
                            "data": [
                                {"cliente": "A", "faturamento": 100},
                                {"cliente": "B", "faturamento": 80},
                            ],
                        }
                    ]
                },
            },
        }
    ]

    analysis = ChatSqlResultAnalyzerService.analyze_tool_calls(tool_calls)

    assert analysis is not None
    assert analysis["rowCount"] == 2
    assert analysis["isEmpty"] is False


def test_visualization_ranking_recommends_horizontal_bar():
    advice = ChatSqlVisualizationAdvisorService.recommend(
        message="mostre ranking de clientes por faturamento",
        mode="execute",
        result_analysis={"rowCount": 5, "isEmpty": False, "columns": ["cliente", "faturamento"]},
    )

    assert advice["chartType"] == "horizontal_bar"
    assert advice["presentationType"] == "chart"


def test_visualization_temporal_recommends_line():
    advice = ChatSqlVisualizationAdvisorService.recommend(
        message="evolucao de vendas por mes",
        mode="create",
    )

    assert advice["chartType"] == "line"


def test_visualization_single_row_recommends_kpi():
    advice = ChatSqlVisualizationAdvisorService.recommend(
        message="interprete resultado",
        mode="analyze_result",
        result_analysis={"rowCount": 1, "isEmpty": False, "columns": ["total_vendas"]},
    )

    assert advice["chartType"] == "kpi"


def test_empty_recovery_follow_ups():
    follow_ups = ChatSqlResultAnalyzerService.build_empty_recovery_follow_ups()

    assert any(item["label"] == "Ampliar período" for item in follow_ups)
