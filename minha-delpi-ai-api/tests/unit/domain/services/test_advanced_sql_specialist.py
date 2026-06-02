"""Regressão Especialista SQL Avançado — Playbook §52."""

from unittest.mock import patch

import pytest

from app.domain.services.chat_advanced_sql_specialist_service import (
    ChatAdvancedSqlSpecialistService,
)
from app.domain.services.chat_sql_dialect_resolver_service import (
    ChatSqlDialectResolverService,
)
from app.domain.services.chat_sql_performance_advisor_service import (
    ChatSqlPerformanceAdvisorService,
)
from app.domain.services.chat_sql_review_service import ChatSqlReviewService
from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService


def _ctx():
    return {"skills": {"sqlAuthoring": True}}


def test_sql1_create_simple_select_mode():
    mode = ChatAdvancedSqlSpecialistService.classify_mode(
        "monte um select de produtos ativos sem executar"
    )

    assert mode == "create"
    assert ChatAdvancedSqlSpecialistService.should_activate(
        "monte um select de produtos ativos",
        workspace_context=_ctx(),
    )


def test_sql2_default_dialect_when_not_informed():
    resolved = ChatSqlDialectResolverService.resolve("monte uma consulta de vendas")

    assert resolved["dialect"] == "sqlserver"
    assert resolved["assumed"] is True
    assert resolved["limitSyntax"] == "TOP n"


def test_sql3_add_column_incremental_mode():
    previous = [
        {
            "role": "assistant",
            "content": "Resultado",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"path": "/data/sql", "ok": True},
                        "arguments": {"sql": "SELECT A1_COD FROM SA1"},
                    }
                ]
            },
        }
    ]

    mode = ChatAdvancedSqlSpecialistService.classify_mode(
        "adicione a coluna cidade na consulta anterior",
        previous_messages=previous,
    )

    assert mode == "incremental_edit"


def test_sql4_remove_column_incremental_mode():
    previous = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"path": "/data/sql", "ok": True},
                        "arguments": {"sql": "SELECT A1_COD, A1_NOME FROM SA1"},
                    }
                ]
            },
        }
    ]

    mode = ChatAdvancedSqlSpecialistService.classify_mode(
        "remova a coluna valor liquido da consulta anterior",
        previous_messages=previous,
    )

    assert mode == "incremental_edit"


def test_sql5_period_compare_planner_hint():
    hints = ChatAdvancedSqlSpecialistService.build_planner_hints(
        "compare vendas deste mes com o mes anterior"
    )

    assert "use_cte_period_compare" in hints


def test_sql6_ranking_window_hint():
    hints = ChatAdvancedSqlSpecialistService.build_planner_hints(
        "monte um ranking de clientes por faturamento"
    )

    assert "use_window_rank" in hints


def test_sql7_top_n_window_hint():
    hints = ChatAdvancedSqlSpecialistService.build_planner_hints(
        "top 5 produtos por categoria"
    )

    assert "use_window_rank" in hints


def test_sql8_last_record_window_hint():
    hints = ChatAdvancedSqlSpecialistService.build_planner_hints(
        "traga o ultimo registro por cliente"
    )

    assert "use_row_number_dedup" in hints


def test_sql9_percent_variation_hint():
    hints = ChatAdvancedSqlSpecialistService.build_planner_hints(
        "calcule a variacao percentual de vendas"
    )

    assert "guard_division_by_zero" in hints


def test_sql10_join_duplicidade_warning():
    analysis = ChatSqlPerformanceAdvisorService.analyze(
        "SELECT DISTINCT c.id, p.valor FROM clientes c JOIN pedidos p ON p.cliente_id = c.id"
    )
    codes = {item["code"] for item in analysis["issues"]}

    assert "distinct_masking_join" in codes


def test_sql11_delete_blocked():
    assert ChatSqlSafetyService.contains_destructive_sql("DELETE FROM SA1 WHERE A1_COD = '001'")

    snapshot = ChatAdvancedSqlSpecialistService.build_pipeline_snapshot(
        message="DELETE FROM SA1",
        workspace_context=_ctx(),
    )

    assert snapshot is not None
    assert snapshot["blocked"] is True


def test_sql12_select_star_suggests_columns():
    analysis = ChatSqlPerformanceAdvisorService.analyze("SELECT * FROM SA1")

    assert any(item["code"] == "select_star" for item in analysis["issues"])


def test_sql13_schema_prefetch_on_explore():
    assert ChatAdvancedSqlSpecialistService.should_prefetch_schema(
        message="quais colunas existem na tabela SB1",
        workspace_context={
            **_ctx(),
            "actionsEnabled": True,
            "allowedActionIds": ["system-columns"],
        },
    )


def test_schema_prefetch_requires_agent_actions():
    assert not ChatAdvancedSqlSpecialistService.should_prefetch_schema(
        message="quais colunas existem na tabela SB1",
        workspace_context=_ctx(),
    )


def test_schema_discovery_snapshot_contains_candidates():
    snapshot = ChatAdvancedSqlSpecialistService.build_pipeline_snapshot(
        message="monte uma consulta de clientes na tabela SB1",
        workspace_context=_ctx(),
    )

    assert snapshot is not None
    assert snapshot["schemaDiscovery"]["tableCandidates"] == ["SB1"]
    assert "cliente" in (snapshot["schemaDiscovery"]["domainHint"] or "").lower()


def test_sql14_empty_result_recovery_mode():
    mode = ChatAdvancedSqlSpecialistService.classify_mode(
        "interprete o resultado vazio da consulta anterior"
    )

    assert mode in {"analyze_result", "execute", "create"}


def test_sql15_slow_query_optimize_mode():
    mode = ChatAdvancedSqlSpecialistService.classify_mode("minha query esta lenta, otimize")

    assert mode == "optimize"


def test_sql16_explain_mode():
    mode = ChatAdvancedSqlSpecialistService.classify_mode(
        "explique essa query: SELECT A1_COD FROM SA1"
    )

    assert mode == "explain"


def test_sql17_review_points_risks():
    review = ChatSqlReviewService.review(
        "SELECT * FROM SA1 JOIN SC5 ON SC5.C5_CLIENTE = SA1.A1_COD"
    )

    assert review["riskLevel"] in {"medium", "high", "low"}
    assert len(review["checklist"]) >= 2


def test_sql18_execute_mode():
    mode = ChatAdvancedSqlSpecialistService.classify_mode(
        "execute essa consulta no banco: SELECT A1_COD FROM SA1"
    )

    assert mode == "execute"


def test_sql19_analyze_result_mode():
    mode = ChatAdvancedSqlSpecialistService.classify_mode(
        "interprete o resultado da ultima consulta sql"
    )

    assert mode == "analyze_result"


def test_sql20_visualize_mode():
    mode = ChatAdvancedSqlSpecialistService.classify_mode(
        "gere um grafico com os dados da ultima consulta"
    )

    assert mode == "visualize"


def test_cte_and_window_detection():
    sql = """
    WITH base AS (SELECT 1 AS x)
    SELECT ROW_NUMBER() OVER (PARTITION BY x ORDER BY x) AS rn FROM base
    """
    analysis = ChatSqlPerformanceAdvisorService.analyze(sql)

    assert analysis["features"]["usesCte"] is True
    assert analysis["features"]["usesWindowFunction"] is True


def test_postgres_dialect_from_message():
    resolved = ChatSqlDialectResolverService.resolve("monte query postgres com limit")

    assert resolved["dialect"] == "postgresql"
    assert resolved["assumed"] is False


def test_enrich_tool_context_adds_supplement():
    result = ChatAdvancedSqlSpecialistService.enrich_tool_context(
        message="monte uma consulta de estoque",
        result={"context": "", "toolCalls": []},
        workspace_context=_ctx(),
    )

    assert "sqlAdvanced" in result
    assert "Especialista SQL Avançado" in result["context"]


def test_follow_up_suggestions_for_review_mode():
    snapshot = ChatAdvancedSqlSpecialistService.build_pipeline_snapshot(
        message="revisa essa query",
        workspace_context=_ctx(),
    )
    suggestions = ChatAdvancedSqlSpecialistService.build_follow_up_suggestions(
        message="revisa essa query",
        snapshot=snapshot,
    )
    labels = {item["label"] for item in suggestions}

    assert "Otimizar query" in labels or "Corrigir riscos" in labels


@patch(
    "app.infrastructure.config.settings.Settings.CHAT_DEFAULT_SQL_DIALECT",
    "postgresql",
)
def test_custom_default_dialect_setting():
    resolved = ChatSqlDialectResolverService.resolve("monte uma consulta")

    assert resolved["dialect"] == "postgresql"
