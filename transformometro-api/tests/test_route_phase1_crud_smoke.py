"""Smokes Nível A — fase 1: crud_routes (catálogos + processo/revisão/medição/etc.).

operationIds literais abaixo alimentam audit_route_test_coverage.
"""

from __future__ import annotations

import pytest

from tests.support.route_smoke_runner import run_route_smoke

OPERATION_IDS = (
    "activate_revisao",
    "create_filial",
    "create_investimento",
    "create_processo",
    "create_processo_instancia",
    "create_recurso",
    "create_recurso_custo",
    "create_revisao",
    "create_setor",
    "create_vinculo",
    "delete_filial",
    "delete_instancia",
    "delete_investimento",
    "delete_processo",
    "delete_recurso",
    "delete_recurso_custo",
    "delete_revisao",
    "delete_setor",
    "delete_vinculo",
    "duplicate_instancia",
    "duplicate_processo",
    "duplicate_revisao",
    "get_filial",
    "get_instancia",
    "get_instancia_contexto",
    "get_medicao",
    "get_processo",
    "get_recurso",
    "get_setor",
    "instancia_matriz_impacto_esforco",
    "list_filiais",
    "list_investimentos",
    "list_processo_instancias",
    "list_processos_calculados",
    "list_recurso_custos",
    "list_recurso_vinculos",
    "list_recursos",
    "list_revisoes",
    "list_setores",
    "list_vinculos",
    "processo_comparativo_revisoes",
    "processo_matriz_impacto_esforco",
    "processo_timeline",
    "put_instancia_contexto",
    "put_revisao_matriz_impacto_esforco",
    "reajuste_recurso_custo",
    "revisao_diagnostico_rateio",
    "revisao_matriz_impacto_esforco",
    "update_filial",
    "update_instancia",
    "update_investimento",
    "update_processo",
    "update_recurso",
    "update_recurso_custo",
    "update_revisao",
    "update_setor",
    "update_vinculo",
    "upsert_medicao",
)


@pytest.mark.parametrize("operation_id", OPERATION_IDS)
def test_route_nivel_a_smoke(operation_id, tm_client, openapi_ops):
    meta = openapi_ops[operation_id]
    run_route_smoke(tm_client, meta)
