"""Testes — mapeamento semântico e resolução de relações SQL."""

from app.domain.services.chat_sql_relationship_resolver_service import (
    ChatSqlRelationshipResolverService,
)
from app.domain.services.chat_sql_schema_discovery_service import (
    ChatSqlSchemaDiscoveryService,
)
from app.domain.services.chat_sql_semantic_schema_mapper_service import (
    ChatSqlSemanticSchemaMapperService,
)


def test_semantic_mapper_cliente_and_produto():
    mapping = ChatSqlSemanticSchemaMapperService.map_message(
        "ranking de clientes por produto vendido"
    )
    terms = {item["term"] for item in mapping["matches"]}

    assert "cliente" in terms
    assert "produto" in terms
    assert "A1_COD" in mapping["matches"][0]["columnPatterns"]


def test_semantic_format_hints():
    mapping = ChatSqlSemanticSchemaMapperService.map_message("vendas por filial")
    hints = ChatSqlSemanticSchemaMapperService.format_hints(mapping)

    assert any("venda" in hint.lower() or "vendas" in hint.lower() for hint in hints)


def test_relationship_resolver_declared_fk():
    resolution = ChatSqlRelationshipResolverService.resolve(
        schema_metadata={
            "relations": [
                {
                    "sourceTable": "SC5",
                    "sourceField": "C5_CLIENTE",
                    "targetTable": "SA1",
                    "targetField": "A1_COD",
                }
            ]
        }
    )

    assert resolution["declaredRelations"][0]["label"] == "SC5.C5_CLIENTE = SA1.A1_COD"


def test_relationship_resolver_infers_from_columns():
    resolution = ChatSqlRelationshipResolverService.resolve(
        schema_metadata={
            "tables": {
                "SC5": {
                    "columns": [
                        {"field": "C5_CLIENTE", "description": "Cliente"},
                        {"field": "C5_NUM", "description": "Pedido"},
                    ]
                },
                "SA1": {"columns": [{"field": "A1_COD", "description": "Código"}]},
            }
        }
    )

    assert resolution["inferredRelations"]
    assert any("C5_CLIENTE" in item["label"] for item in resolution["inferredRelations"])


def test_schema_snapshot_includes_semantic_and_relationships():
    snapshot = ChatSqlSchemaDiscoveryService.build_schema_snapshot(
        message="relacionar pedidos SC5 com clientes SA1",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {"path": "/system/tables/SC5/relations", "ok": True},
                "result": {
                    "results": [
                        {
                            "X9_DOM": "SC5",
                            "X9_CAMPO": "C5_CLIENTE",
                            "X9_TABELA": "SA1",
                            "X9_CAMPO_DESTINO": "A1_COD",
                        }
                    ]
                },
            }
        ],
    )

    assert snapshot["semanticMapping"]["hasMatches"]
    assert snapshot["relationships"]["declaredRelations"]
    assert "SC5" in snapshot["tableCandidates"]
