"""Smokes Nível A — fase 0: health / options / prova do harness.

operationIds literais abaixo alimentam audit_route_test_coverage.
"""

from __future__ import annotations

import pytest

from tests.support.route_smoke_runner import run_route_smoke

OPERATION_IDS = (
    "get_options",
    "health",
    "list_processos",
    "module_health",
)


@pytest.mark.parametrize("operation_id", OPERATION_IDS)
def test_route_nivel_a_smoke(operation_id, tm_client, openapi_ops):
    meta = openapi_ops[operation_id]
    run_route_smoke(tm_client, meta)
