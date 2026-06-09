"""Matriz de regressão — «por filial» em produção, estoque e refinamento SQL."""

from __future__ import annotations

from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)
from app.domain.services.chat_sql_inventory_query_service import (
    ChatSqlInventoryQueryService,
)
from app.domain.services.chat_sql_production_query_service import (
    ChatSqlProductionQueryService,
)
from app.domain.services.chat_sql_query_refinement_service import (
    ChatSqlQueryRefinementService,
)


class FakeRepository:
    def __init__(self, actions):
        self.actions = actions

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        allowed = set(allowed_action_ids or [])
        return [
            action
            for action in self.actions
            if not allowed or action["actionId"] in allowed
        ]

    def list_actions(self):
        return self.actions


SQL_ACTION = "api_delpi.data.execute_readonly_sql"
SQL_ACTIONS = [
    {
        "actionId": SQL_ACTION,
        "method": "POST",
        "path": "/data/sql",
        "summary": "Executar SQL somente leitura",
    }
]


def _history(sql: str, *, title: str = "Consulta SQL"):
    return [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/data/sql",
                            "sensitivity": "sql",
                            "executedSql": sql,
                            "presentation": {"type": "table", "title": title},
                        },
                    }
                ]
            },
        }
    ]


def _select(message: str, *, history=None):
    service = ExternalActionSelectionService(FakeRepository(SQL_ACTIONS))
    return service.select_action(
        message,
        allowed_action_ids=[SQL_ACTION],
        previous_messages=history or [],
    )


# --- Produção (fast path SC2010) ---


def test_production_tomorrow_by_branch_exact_user_message():
    resolution = ChatSqlProductionQueryService.resolve(
        "o que está programado para produzir amanhã por filial?"
    )

    assert resolution is not None
    assert "OP.C2_FILIAL AS FILIAL" in resolution.sql
    assert "OP.C2_FILIAL IN ('01', '02')" in resolution.sql
    assert "por filial" in resolution.title.lower()


def test_production_today_by_branch_includes_all_branches():
    resolution = ChatSqlProductionQueryService.resolve(
        "o que sera produzido hoje por filial?"
    )

    assert resolution is not None
    assert "OP.C2_FILIAL AS FILIAL" in resolution.sql
    assert "OP.C2_FILIAL IN ('01', '02')" in resolution.sql


def test_production_tomorrow_all_branches_synonym():
    resolution = ChatSqlProductionQueryService.resolve(
        "programacao de producao amanha todas as filiais"
    )

    assert resolution is not None
    assert "OP.C2_FILIAL IN ('01', '02')" in resolution.sql


def test_production_explicit_branch_keeps_single_branch_filter():
    resolution = ChatSqlProductionQueryService.resolve(
        "o que sera produzido amanha filial 02?"
    )

    assert resolution is not None
    assert "DECLARE @FILIAL CHAR(2) = '02';" in resolution.sql
    assert "AS FILIAL" not in resolution.sql


def test_production_dispatch_prefers_fast_path_over_stale_refinement():
    stale_sql = ChatSqlProductionQueryService.resolve(
        "o que sera produzido amanha?"
    ).sql
    selected = _select(
        "o que esta programado para produzir amanha por filial?",
        history=_history(stale_sql, title="Programação amanhã"),
    )

    assert selected is not None
    sql = selected["arguments"]["body"]["sql"]
    assert "OP.C2_FILIAL AS FILIAL" in sql
    assert "OP.C2_FILIAL IN ('01', '02')" in sql
    assert "productionSqlFastPath" in selected.get("reason", "").lower() or (
        "programação" in selected["reason"].lower()
        or "produção" in selected["reason"].lower()
    )


# --- Estoque (fast path SB2010) ---


def test_inventory_below_minimum_already_has_branch_column():
    resolution = ChatSqlInventoryQueryService.resolve(
        "liste os produtos com estoque abaixo do minimo por filial"
    )

    assert resolution is not None
    assert "SB2.B2_FILIAL AS branch" in resolution.sql
    assert "AND SB2.B2_FILIAL =" not in resolution.sql


def test_inventory_all_branches_no_filter():
    resolution = ChatSqlInventoryQueryService.resolve(
        "produtos com estoque abaixo do minimo todas as filiais"
    )

    assert resolution is not None
    assert "SB2.B2_FILIAL AS branch" in resolution.sql
    assert "AND SB2.B2_FILIAL" not in resolution.sql


def test_inventory_single_branch_filter():
    resolution = ChatSqlInventoryQueryService.resolve(
        "estoque abaixo do minimo filial 01"
    )

    assert resolution is not None
    assert "AND SB2.B2_FILIAL = '01'" in resolution.sql


def test_inventory_refinement_filial_01_e_02():
    base_sql = ChatSqlInventoryQueryService.resolve(
        "liste os produtos com estoque abaixo do minimo"
    ).sql
    refinement = ChatSqlQueryRefinementService.resolve(
        "filial 01 e 02",
        previous_messages=_history(base_sql),
    )

    assert refinement is not None
    assert "SB2.B2_FILIAL IN ('01', '02')" in refinement.sql


# --- Refinamento multi-turn ---


def test_refinement_por_filial_expands_sc2010_only():
    single_branch = ChatSqlProductionQueryService.resolve(
        "o que sera produzido amanha?"
    ).sql
    refinement = ChatSqlQueryRefinementService.resolve(
        "detalhe por filial",
        previous_messages=_history(single_branch),
    )

    assert refinement is not None
    assert "OP.C2_FILIAL AS FILIAL" in refinement.sql
    assert "OP.C2_FILIAL IN ('01', '02')" in refinement.sql


def test_refinement_por_filial_does_not_break_inventory_sql():
    inventory_sql = ChatSqlInventoryQueryService.resolve(
        "liste os produtos com estoque abaixo do minimo"
    ).sql
    refinement = ChatSqlQueryRefinementService.resolve(
        "detalhe por filial",
        previous_messages=_history(inventory_sql),
    )

    # Estoque já traz coluna branch; expand_production_sql_by_branch não altera SB2010.
    assert refinement is None


def test_refinement_add_filial_column_on_production():
    single_branch = ChatSqlProductionQueryService.resolve(
        "o que sera produzido segunda feira?"
    ).sql
    refinement = ChatSqlQueryRefinementService.resolve(
        "acrescente a coluna de filial",
        previous_messages=_history(single_branch),
    )

    assert refinement is not None
    assert "OP.C2_FILIAL AS FILIAL" in refinement.sql


def test_expand_production_sql_ignores_non_production_sql():
    customer_sql = "SELECT A1_COD, A1_NOME FROM SA1010 WHERE D_E_L_E_T_ = ''"
    expanded = ChatSqlProductionQueryService.expand_production_sql_by_branch(customer_sql)

    assert expanded == customer_sql
