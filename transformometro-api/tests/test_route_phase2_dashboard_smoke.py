"""Smokes Nível A — fase 2: dashboard_routes + integrations_routes.

operationIds literais abaixo alimentam audit_route_test_coverage.
"""

from __future__ import annotations

import pytest

from tests.support.route_smoke_runner import run_route_smoke

OPERATION_IDS = (
    "dashboard_alertas",
    "dashboard_evolucao",
    "dashboard_export_csv",
    "dashboard_export_excel",
    "dashboard_por_familia",
    "dashboard_processos",
    "dashboard_resumo",
    "dashboard_vencimentos",
    "get_dashboard_snapshot_instancias",
    "get_dashboard_snapshot_linhas",
    "get_dashboard_snapshot_meta",
    "get_dashboard_snapshot_processos",
    "get_dashboard_snapshot_resumo",
    "integration_list_processes",
    "integration_process_summary",
    "recalcular_dashboard",
)


@pytest.mark.parametrize("operation_id", OPERATION_IDS)
def test_route_nivel_a_smoke(operation_id, tm_client, openapi_ops):
    meta = openapi_ops[operation_id]
    run_route_smoke(tm_client, meta)
