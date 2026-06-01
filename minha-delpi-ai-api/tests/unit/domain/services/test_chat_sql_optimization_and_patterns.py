"""Testes — otimização e padrões SQL avançados."""

from app.domain.services.chat_sql_optimization_advisor_service import (
    ChatSqlOptimizationAdvisorService,
)
from app.domain.services.chat_sql_query_pattern_advisor_service import (
    ChatSqlQueryPatternAdvisorService,
)


def test_optimization_advisor_index_hints():
    advice = ChatSqlOptimizationAdvisorService.advise(
        "SELECT A1_COD FROM SA1010 WHERE A1_FILIAL = '01' ORDER BY A1_NOME",
        dialect="sqlserver",
        mode="optimize",
    )

    codes = {item["code"] for item in advice["suggestions"]}

    assert "index_filter_column" in codes or "index_sort_column" in codes
    assert advice["explainRecommended"] is True


def test_optimization_explain_unavailable_message():
    advice = ChatSqlOptimizationAdvisorService.advise(
        "SELECT * FROM SA1",
        mode="optimize",
        explain_available=False,
    )

    explain_items = [item for item in advice["suggestions"] if item.get("category") == "explain"]

    assert explain_items
    assert explain_items[0]["code"] == "explain_unavailable"


def test_pattern_advisor_period_compare():
    advice = ChatSqlQueryPatternAdvisorService.recommend(
        "compare vendas deste mes com o mes anterior"
    )

    assert "period_compare_cte" in advice["hints"]
    assert any(item["code"] == "period_compare_cte" for item in advice["patterns"])


def test_pattern_advisor_window_rank():
    advice = ChatSqlQueryPatternAdvisorService.recommend("ranking de clientes por faturamento")

    assert "window_rank" in advice["hints"]
