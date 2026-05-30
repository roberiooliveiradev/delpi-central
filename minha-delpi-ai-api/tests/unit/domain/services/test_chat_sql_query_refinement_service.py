from app.domain.services.chat_sql_production_query_service import (
    ChatSqlProductionQueryService,
)
from app.domain.services.chat_sql_query_refinement_service import (
    ChatSqlQueryRefinementService,
)


SAMPLE_SQL = ChatSqlProductionQueryService.resolve(
    "o que sera produzido segunda feira?"
).sql


def _history_with_sql(sql: str = SAMPLE_SQL):
    return [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "api_externa.data.execute_sql_raw_data_sql_post",
                            "body": {"sql": sql},
                        },
                        "metadata": {
                            "ok": True,
                            "path": "/data/sql",
                            "sensitivity": "sql",
                            "executedSql": sql,
                            "presentation": {
                                "title": "Produtos programados para produção segunda-feira (01/06/2026)",
                            },
                        },
                    }
                ]
            },
        }
    ]


def test_add_filial_column_to_previous_sql():
    refinement = ChatSqlQueryRefinementService.resolve(
        "acrescente a coluna de filial",
        previous_messages=_history_with_sql(),
    )

    assert refinement is not None
    assert refinement.mode == "execute"
    assert "OP.C2_FILIAL AS FILIAL" in refinement.sql
    assert "OP.C2_FILIAL" in refinement.sql.split("GROUP BY", 1)[1]


def test_show_sql_from_history():
    refinement = ChatSqlQueryRefinementService.resolve(
        "mostre a query usada",
        previous_messages=_history_with_sql(),
    )

    assert refinement is not None
    assert refinement.mode == "show_sql"
    assert "SC2010" in refinement.sql


def test_apply_branch_filter():
    updated = ChatSqlQueryRefinementService.apply_branch_filter(SAMPLE_SQL, "02")

    assert "DECLARE @FILIAL CHAR(2) = '02';" in updated


def test_remove_column():
    sql_with_filial = ChatSqlQueryRefinementService.add_column(SAMPLE_SQL, "filial")
    updated = ChatSqlQueryRefinementService.remove_column(sql_with_filial, "filial")

    assert "AS FILIAL" not in updated


def test_does_not_match_without_history():
    assert (
        ChatSqlQueryRefinementService.resolve(
            "acrescente a coluna de filial",
            previous_messages=[],
        )
        is None
    )
