"""Casos SQL1–SQL20 — Playbook Especialista SQL Avançado §52."""

from __future__ import annotations

ADVANCED_SQL_SPECIALIST_REGRESSION_CASES: list[dict] = [
    {"id": "SQL1", "message": "monte um select de produtos ativos", "mode": "create", "activate": True},
    {"id": "SQL2", "message": "monte uma consulta de vendas", "dialect": "sqlserver", "assumed": True},
    {
        "id": "SQL3",
        "message": "adicione a coluna cidade na consulta anterior",
        "mode": "incremental_edit",
        "history_sql": "SELECT A1_COD FROM SA1",
    },
    {
        "id": "SQL4",
        "message": "remova a coluna valor liquido da consulta anterior",
        "mode": "incremental_edit",
        "history_sql": "SELECT A1_COD, A1_NOME FROM SA1",
    },
    {"id": "SQL5", "message": "compare vendas deste mes com o mes anterior", "planner_hint": "use_cte_period_compare"},
    {"id": "SQL6", "message": "monte um ranking de clientes por faturamento", "planner_hint": "use_window_rank"},
    {"id": "SQL7", "message": "top 5 produtos por categoria", "planner_hint": "use_window_rank"},
    {"id": "SQL8", "message": "traga o ultimo registro por cliente", "planner_hint": "use_row_number_dedup"},
    {"id": "SQL9", "message": "calcule a variacao percentual de vendas", "planner_hint": "guard_division_by_zero"},
    {
        "id": "SQL10",
        "message": "join clientes e pedidos",
        "duplicate_risk": True,
        "tables": ["SA1", "SC5"],
    },
    {"id": "SQL11", "message": "DELETE FROM SA1", "blocked": True},
    {"id": "SQL12", "sql": "SELECT * FROM SA1", "performance_code": "select_star"},
    {"id": "SQL13", "message": "quais colunas existem na tabela SB1", "prefetch_schema": True, "mode": "schema_explore"},
    {"id": "SQL14", "message": "interprete o resultado vazio da consulta anterior", "mode": "analyze_result"},
    {"id": "SQL15", "message": "minha query esta lenta, otimize", "mode": "optimize"},
    {"id": "SQL16", "message": "explique essa query: SELECT A1_COD FROM SA1", "mode": "explain"},
    {"id": "SQL17", "message": "revisa essa query", "mode": "review", "sql": "SELECT * FROM SA1"},
    {"id": "SQL18", "message": "execute essa consulta no banco: SELECT A1_COD FROM SA1", "mode": "execute"},
    {"id": "SQL19", "message": "interprete o resultado da ultima consulta sql", "mode": "analyze_result"},
    {"id": "SQL20", "message": "gere um grafico com os dados da ultima consulta", "mode": "visualize"},
    {"id": "SQL_SEM", "message": "consulta de clientes por cidade", "semantic_term": "cliente"},
]
