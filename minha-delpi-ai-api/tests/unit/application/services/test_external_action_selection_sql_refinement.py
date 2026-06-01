from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)
from app.domain.services.chat_sql_production_query_service import (
    ChatSqlProductionQueryService,
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


def test_select_action_sql_refinement_adds_filial_column():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "api_externa.data.execute_sql_raw_data_sql_post",
                    "method": "POST",
                    "path": "/data/sql",
                    "summary": "Executar SQL somente leitura",
                }
            ]
        )
    )
    sql = ChatSqlProductionQueryService.resolve(
        "o que sera produzido segunda feira?"
    ).sql
    history = [
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
                        },
                    }
                ]
            },
        }
    ]

    selected = service.select_action(
        "acrescente a coluna de filial",
        allowed_action_ids=["api_externa.data.execute_sql_raw_data_sql_post"],
        previous_messages=history,
    )

    assert selected is not None
    assert "OP.C2_FILIAL AS FILIAL" in selected["arguments"]["body"]["sql"]
    assert "Refinamento da consulta SQL anterior" in selected["reason"]


def test_select_action_inventory_below_minimum_uses_sb2010_sql():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "api_delpi.data.execute_readonly_sql",
                    "method": "POST",
                    "path": "/data/sql",
                    "summary": "Executar SQL somente leitura",
                }
            ]
        )
    )

    selected = service.select_action(
        "Liste os produtos com estoque abaixo do mínimo",
        allowed_action_ids=["api_delpi.data.execute_readonly_sql"],
    )

    assert selected is not None
    sql = selected["arguments"]["body"]["sql"]
    assert "SB2010" in sql
    assert "B1_EMIN" in sql
    assert "SBZ010" in sql
    assert "SC2010" not in sql
    assert "estoque abaixo do mínimo" in selected["reason"].lower()


def test_select_action_sql_refinement_filters_inventory_branches():
    from app.domain.services.chat_sql_inventory_query_service import (
        ChatSqlInventoryQueryService,
    )

    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "api_delpi.data.execute_readonly_sql",
                    "method": "POST",
                    "path": "/data/sql",
                    "summary": "Executar SQL somente leitura",
                }
            ]
        )
    )
    sql = ChatSqlInventoryQueryService.resolve(
        "liste os produtos com estoque abaixo do minimo"
    ).sql
    history = [
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
                        },
                    }
                ]
            },
        }
    ]

    selected = service.select_action(
        "filial 01 e 02",
        allowed_action_ids=["api_delpi.data.execute_readonly_sql"],
        previous_messages=history,
    )

    assert selected is not None
    assert "SB2.B2_FILIAL IN ('01', '02')" in selected["arguments"]["body"]["sql"]
    assert "Refinamento da consulta SQL anterior" in selected["reason"]
