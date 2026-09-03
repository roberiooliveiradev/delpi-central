"""GetTableSchemaUseCase — contrato composite_analysis com seções {items,total,truncated}."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.system.system_requests import GetTableSchemaRequest
from app.application.use_cases.system.get_table_schema_use_case import GetTableSchemaUseCase


def test_get_table_schema_returns_composite_section_blocks():
    repository = MagicMock()
    repository.get_table.return_value = [
        {"X2_CHAVE": "SB1", "X2_ARQUIVO": "SB1010", "X2_NOME": "Produtos", "TableName": "SB1010"},
    ]
    repository.get_columns_table.return_value = {
        "total": 2,
        "results": [
            {"X3_CAMPO": "B1_COD", "X3_DESCRIC": "Codigo"},
            {"X3_CAMPO": "B1_DESC", "X3_DESCRIC": "Descricao"},
        ],
    }
    repository.get_table_indexes.return_value = [{"INDICE": "SB1", "ORDEM": "1"}]
    repository.get_table_relations.return_value = [{"X9_DOM": "SB1", "X9_CAMPO": "B1_COD"}]

    result = GetTableSchemaUseCase(repository).execute(
        GetTableSchemaRequest(table_name="SB1010")
    )

    assert result["summary"]["tableName"] == "SB1010"
    assert result["summary"]["alias"] == "SB1"
    assert result["summary"]["columnCount"] == 2
    assert result["columns"]["total"] == 2
    assert result["columns"]["truncated"] is False
    assert result["columns"]["items"][0]["X3_CAMPO"] == "B1_COD"
    assert isinstance(result["indexes"], dict) and result["indexes"]["items"]
    assert isinstance(result["table"], dict) and result["table"]["items"][0]["X2_CHAVE"] == "SB1"

    sections = GetTableSchemaUseCase.build_sections(result)
    assert [section["key"] for section in sections] == [
        "columns",
        "indexes",
        "relations",
        "table",
    ]
    assert sections[0]["itemCount"] == 2


def test_get_table_schema_paginates_columns_and_truncates_relations():
    repository = MagicMock()
    repository.get_table.return_value = {"X2_CHAVE": "SB1", "X2_ARQUIVO": "SB1010"}
    repository.get_columns_table.side_effect = [
        {
            "total": 3,
            "results": [
                {"X3_CAMPO": "B1_COD"},
                {"X3_CAMPO": "B1_DESC"},
            ],
        },
        {
            "total": 3,
            "results": [{"X3_CAMPO": "B1_TIPO"}],
        },
    ]
    repository.get_table_indexes.return_value = []
    repository.get_table_relations.return_value = [
        {"X9_DOM": "SB1", "X9_CAMPO": f"C{i}"} for i in range(150)
    ]

    result = GetTableSchemaUseCase(repository).execute(
        GetTableSchemaRequest(table_name="SB1010")
    )

    assert [row["X3_CAMPO"] for row in result["columns"]["items"]] == [
        "B1_COD",
        "B1_DESC",
        "B1_TIPO",
    ]
    assert repository.get_columns_table.call_count == 2
    assert result["relations"]["total"] == 150
    assert result["relations"]["truncated"] is True
    assert len(result["relations"]["items"]) == 100
    assert result["summary"]["relationCount"] == 150
