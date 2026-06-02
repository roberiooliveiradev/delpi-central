"""Testes para descoberta de schema SQL e metadados."""

from app.domain.services.chat_sql_schema_discovery_service import (
    ChatSqlSchemaDiscoveryService,
)


def test_extract_table_candidates_from_message():
    candidates = ChatSqlSchemaDiscoveryService.extract_table_candidates(
        "monte uma query usando a tabela SB1 e também SA1"
    )

    assert candidates == ["SB1", "SA1"]


def test_extract_column_candidates_from_message():
    candidates = ChatSqlSchemaDiscoveryService.extract_column_candidates(
        "traga a coluna valor_liquido e o campo A1_COD"
    )

    assert "VALOR_LIQUIDO" in candidates
    assert "A1_COD" in candidates


def test_collect_schema_metadata_from_tool_calls():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "path": "/system/tables/SB1/columns",
                "ok": True,
            },
            "result": {
                "results": [
                    {"X3_CAMPO": "A1_COD", "X3_DESCRIC": "Código"},
                    {"X3_CAMPO": "A1_NOME", "X3_DESCRIC": "Nome"},
                ]
            },
        }
    ]

    schema = ChatSqlSchemaDiscoveryService.collect_schema_metadata(tool_calls)

    assert schema["tables"]["SB1"]["columns"][0]["field"] == "A1_COD"
    assert schema["tables"]["SB1"]["columns"][1]["field"] == "A1_NOME"
    assert schema["tables"]["SB1"]["columns"][0]["description"] == "Código"


def test_build_schema_snapshot_includes_candidates_and_metadata():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {"path": "/system/tables/SB1/columns", "ok": True},
            "result": {
                "results": [{"X3_CAMPO": "A1_COD", "X3_DESCRIC": "Código"}],
            },
        }
    ]

    snapshot = ChatSqlSchemaDiscoveryService.build_schema_snapshot(
        message="consulta de clientes na tabela SB1",
        tool_calls=tool_calls,
    )

    assert snapshot["tableCandidates"] == ["SB1"]
    assert "cliente" in snapshot["domainHint"].lower()
    assert snapshot["metadata"]["tables"]["SB1"]["columns"]
