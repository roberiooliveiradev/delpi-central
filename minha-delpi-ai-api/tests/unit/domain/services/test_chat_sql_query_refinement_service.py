from app.domain.services.chat_sql_inventory_query_service import (
    ChatSqlInventoryQueryService,
)
from app.domain.services.chat_sql_production_query_service import (
    ChatSqlProductionQueryService,
)
from app.domain.services.chat_sql_query_refinement_service import (
    ChatSqlQueryRefinementService,
)


SAMPLE_SQL = ChatSqlProductionQueryService.resolve(
    "o que sera produzido segunda feira?"
).sql

INVENTORY_SQL = ChatSqlInventoryQueryService.resolve(
    "liste os produtos com estoque abaixo do minimo"
).sql


def _history_with_sql(sql: str = SAMPLE_SQL, *, title: str | None = None):
    presentation_title = title or "Consulta SQL"

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
                                "type": "table",
                                "title": presentation_title,
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


def test_apply_branch_filter_production():
    updated = ChatSqlQueryRefinementService.apply_branch_filter(SAMPLE_SQL, ["02"])

    assert "DECLARE @FILIAL CHAR(2) = '02';" in updated


def test_apply_branch_filter_inventory_single_branch():
    updated = ChatSqlQueryRefinementService.apply_branch_filter(INVENTORY_SQL, ["01"])

    assert "SB2.B2_FILIAL = '01'" in updated


def test_apply_branch_filter_inventory_multiple_branches():
    updated = ChatSqlQueryRefinementService.apply_branch_filter(INVENTORY_SQL, ["01", "02"])

    assert "SB2.B2_FILIAL IN ('01', '02')" in updated


def test_resolve_filial_01_e_02_after_inventory_sql():
    refinement = ChatSqlQueryRefinementService.resolve(
        "filial 01 e 02",
        previous_messages=_history_with_sql(
            INVENTORY_SQL,
            title="Produtos com estoque abaixo do mínimo",
        ),
    )

    assert refinement is not None
    assert refinement.mode == "execute"
    assert "SB2.B2_FILIAL IN ('01', '02')" in refinement.sql


def test_resolve_por_filial_expands_production_sql():
    refinement = ChatSqlQueryRefinementService.resolve(
        "detalhe por filial",
        previous_messages=_history_with_sql(),
    )

    assert refinement is not None
    assert refinement.mode == "execute"
    assert "OP.C2_FILIAL AS FILIAL" in refinement.sql
    assert "OP.C2_FILIAL IN ('01', '02')" in refinement.sql


def test_remove_branch_filter_inventory():
    filtered = ChatSqlQueryRefinementService.apply_branch_filter(INVENTORY_SQL, ["01"])
    updated = ChatSqlQueryRefinementService.remove_branch_filter(filtered)

    assert "AND SB2.B2_FILIAL" not in updated


def test_apply_top_limit():
    updated = ChatSqlQueryRefinementService.apply_top_limit(INVENTORY_SQL, 50)

    assert "SELECT TOP 50" in updated


def test_resolve_top_limit_follow_up():
    refinement = ChatSqlQueryRefinementService.resolve(
        "top 50",
        previous_messages=_history_with_sql(INVENTORY_SQL),
    )

    assert refinement is not None
    assert refinement.mode == "execute"
    assert "SELECT TOP 50" in refinement.sql


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


CUSTOMER_SQL = "SELECT A1_COD, A1_NOME\nFROM SA1010\nWHERE D_E_L_E_T_ = ''"


def test_filter_query_by_row_value_uses_code_column():
    refinement = ChatSqlQueryRefinementService.resolve(
        "filtre a consulta — A1 cod: 000167; A1 nome: CARLOS ROBERTO DOS SANTOS",
        previous_messages=_history_with_sql(CUSTOMER_SQL, title="Consulta SQL"),
    )

    assert refinement is not None
    assert refinement.mode == "execute"
    assert "RTRIM(A1_COD) = '000167'" in refinement.sql
    # Não filtra por nome (coluna não identificadora) para evitar zerar o resultado.
    assert "A1_NOME" not in refinement.sql.split("WHERE", 1)[1]
    assert "product" not in refinement.reason.lower()


def test_filter_query_by_row_value_without_code_uses_all_columns():
    sql = "SELECT A1_MUN, A1_EST\nFROM SA1010\nWHERE D_E_L_E_T_ = ''"

    refinement = ChatSqlQueryRefinementService.resolve(
        "filtre a consulta — A1 mun: JARAGUA DO SUL; A1 est: SC",
        previous_messages=_history_with_sql(sql),
    )

    assert refinement is not None
    assert "RTRIM(A1_MUN) = 'JARAGUA DO SUL'" in refinement.sql
    assert "RTRIM(A1_EST) = 'SC'" in refinement.sql


def test_filter_query_escapes_single_quote():
    sql = "SELECT A1_COD, A1_NOME\nFROM SA1010"

    refinement = ChatSqlQueryRefinementService.resolve(
        "filtre a consulta — A1 nome: MALHARIA D'ITALIA",
        previous_messages=_history_with_sql(sql),
    )

    assert refinement is not None
    assert "RTRIM(A1_NOME) = 'MALHARIA D''ITALIA'" in refinement.sql
    assert "WHERE" in refinement.sql


def test_filter_query_is_recognized_as_sql_follow_up():
    assert ChatSqlQueryRefinementService.is_sql_follow_up(
        "filtre a consulta — A1 cod: 000167; A1 nome: CARLOS ROBERTO DOS SANTOS",
        previous_messages=_history_with_sql(CUSTOMER_SQL),
    )


def test_filter_query_ignores_columns_absent_from_sql():
    refinement = ChatSqlQueryRefinementService.resolve(
        "filtre a consulta — B1 cod: 10080022",
        previous_messages=_history_with_sql(CUSTOMER_SQL),
    )

    assert refinement is None


PRODUCT_GROUP_SQL = """SELECT TOP 5 B1_COD, B1_DESC
FROM SB1010
WHERE D_E_L_E_T_ = ''
  AND B1_GRUPO = '1008'"""


def _history_with_authoring_sql(sql: str):
    return [
        {
            "role": "assistant",
            "content": f"Segue a consulta.\n\n```sql\n{sql}\n```",
        }
    ]


def test_resolve_execute_active_query_from_session_authoring():
    refinement = ChatSqlQueryRefinementService.resolve(
        "execute essa query e traga os 5 produtos do grupo 1008",
        previous_messages=_history_with_authoring_sql(PRODUCT_GROUP_SQL),
    )

    assert refinement is not None
    assert refinement.mode == "execute"
    assert "SB1010" in refinement.sql
    assert "TOP 5" in refinement.sql.upper()
    assert "B1_GRUPO" in refinement.sql
