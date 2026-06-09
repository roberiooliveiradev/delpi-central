from app.domain.services.chat_sql_dynamic_column_refinement_service import (
    ChatSqlDynamicColumnRefinementService,
)
from app.domain.services.chat_sql_production_query_service import (
    ChatSqlProductionQueryService,
)
from app.domain.services.chat_sql_query_refinement_service import (
    ChatSqlQueryRefinementService,
)


CUSTOMER_SQL = (
    "SELECT A1_COD, A1_NOME, A1_MUN\n"
    "FROM SA1010\n"
    "WHERE D_E_L_E_T_ = ''\n"
    "ORDER BY A1_NOME"
)

PRODUCTION_SQL = ChatSqlProductionQueryService.resolve(
    "o que sera produzido segunda feira?"
).sql


def _history(sql: str):
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
                        },
                    }
                ]
            },
        }
    ]


def test_match_column_by_alias_and_synonym():
    columns = ChatSqlQueryRefinementService.selected_columns(PRODUCTION_SQL)

    assert ChatSqlDynamicColumnRefinementService.match_column("cod produto", PRODUCTION_SQL)
    assert ChatSqlDynamicColumnRefinementService.match_column("produto", PRODUCTION_SQL)
    assert "COD_PRODUTO" in columns


def test_apply_group_by_when_query_has_no_group_by():
    updated = ChatSqlDynamicColumnRefinementService.apply_group_by(
        CUSTOMER_SQL,
        "A1_MUN",
        "A1_MUN",
    )

    assert "GROUP BY" in updated
    assert "A1_MUN" in updated
    assert "SUM(" not in updated


def test_apply_group_by_adds_numeric_aggregation():
    sql = (
        "SELECT A1_COD, A1_NOME, TOTAL_VENDAS\n"
        "FROM SA1010\n"
        "WHERE D_E_L_E_T_ = ''"
    )
    updated = ChatSqlDynamicColumnRefinementService.apply_group_by(
        sql,
        "A1_MUN",
        "A1_MUN",
    )

    assert "GROUP BY" in updated
    assert "SUM(TOTAL_VENDAS)" in updated


def test_apply_group_by_on_existing_group_by():
    updated = ChatSqlDynamicColumnRefinementService.apply_group_by(
        PRODUCTION_SQL,
        "FILIAL",
        "OP.C2_FILIAL",
    )

    assert "OP.C2_FILIAL AS FILIAL" in updated
    assert "OP.C2_FILIAL" in updated.split("GROUP BY", 1)[1]


def test_resolve_group_by_phrase_via_refinement_service():
    refinement = ChatSqlQueryRefinementService.resolve(
        "agrupar por municipio",
        previous_messages=_history(CUSTOMER_SQL),
    )

    assert refinement is not None
    assert refinement.mode == "execute"
    assert "GROUP BY" in refinement.sql
    assert "A1_MUN" in refinement.sql
    assert "agrupamento" in refinement.reason.lower()


def test_resolve_filter_by_column_via_refinement_service():
    refinement = ChatSqlQueryRefinementService.resolve(
        "filtrar por cod produto 90264130",
        previous_messages=_history(PRODUCTION_SQL),
    )

    assert refinement is not None
    assert "RTRIM(OP.C2_PRODUTO) = '90264130'" in refinement.sql
    assert "filtro" in refinement.reason.lower()


def test_resolve_filter_by_column_with_equals_syntax():
    refinement = ChatSqlQueryRefinementService.resolve(
        "filtre descricao produto = PARAFUSO",
        previous_messages=_history(PRODUCTION_SQL),
    )

    assert refinement is not None
    assert "RTRIM(P.B1_DESC) = 'PARAFUSO'" in refinement.sql


def test_resolve_group_by_prefers_explicit_agrupar_over_branch_breakdown():
    refinement = ChatSqlQueryRefinementService.resolve(
        "agrupar por filial",
        previous_messages=_history(PRODUCTION_SQL),
    )

    assert refinement is not None
    assert "OP.C2_FILIAL" in refinement.sql.split("GROUP BY", 1)[1]
    assert "IN ('01', '02')" not in refinement.sql


def test_filtrar_prefix_does_not_trigger_branch_filter():
    refinement = ChatSqlQueryRefinementService.resolve(
        "filtrar por cod produto 90264130",
        previous_messages=_history(PRODUCTION_SQL),
    )

    assert refinement is not None
    assert "RTRIM(OP.C2_PRODUTO) = '90264130'" in refinement.sql
    assert "DECLARE @FILIAL CHAR(2) = '90';" not in refinement.sql


def test_resolve_returns_none_when_column_unknown():
    assert (
        ChatSqlQueryRefinementService.resolve(
            "agrupar por fornecedor inexistente",
            previous_messages=_history(CUSTOMER_SQL),
        )
        is None
    )
