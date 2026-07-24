"""Smokes Nível A — fase 3: diagram_routes + decomposition_routes.

operationIds literais abaixo alimentam audit_route_test_coverage.
"""

from __future__ import annotations

import pytest

from tests.support.route_smoke_runner import run_route_smoke

OPERATION_IDS = (
    "get_diagrama_catalogo",
    "get_instancia_decomposicao_escopo",
    "get_instancia_diagrama_escopo",
    "get_processo_decomposicao",
    "get_processo_decomposicao_composed",
    "get_processo_decomposicao_export_csv",
    "get_processo_diagrama",
    "get_processo_diagrama_bpmn_xml",
    "get_processo_diagrama_composed",
    "get_revisao_decomposicao_merged",
    "get_revisao_decomposicao_overlay",
    "get_revisao_diagrama_merged",
    "get_revisao_diagrama_mermaid",
    "get_revisao_diagrama_overlay",
    "post_processo_diagrama_validacao",
    "post_sugerir_rascunho_decomposicao",
    "post_validar_vinculos_fluxo",
    "put_instancia_decomposicao_escopo",
    "put_instancia_diagrama_escopo",
    "put_processo_decomposicao",
    "put_processo_diagrama",
    "put_processo_diagrama_bpmn_xml",
    "put_revisao_decomposicao_overlay",
    "put_revisao_diagrama_overlay",
)


@pytest.mark.parametrize("operation_id", OPERATION_IDS)
def test_route_nivel_a_smoke(operation_id, tm_client, openapi_ops):
    meta = openapi_ops[operation_id]
    run_route_smoke(tm_client, meta)
