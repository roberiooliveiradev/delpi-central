"""Smokes Nível A — fase 4: evidência, arquivos, backup, collaboration.

operationIds literais abaixo alimentam audit_route_test_coverage.
"""

from __future__ import annotations

import pytest

from tests.support.route_smoke_runner import run_route_smoke

OPERATION_IDS = (
    "attach_processo_arquivo",
    "attach_revisao_evidencia",
    "delete_presenca",
    "delete_processo_arquivo",
    "delete_revisao_evidencia",
    "download_processo_arquivo",
    "download_revisao_evidencia",
    "export_json",
    "export_package",
    "get_presenca",
    "import_apply",
    "import_package_apply",
    "import_package_preview",
    "import_preview",
    "list_processo_arquivos",
    "list_revisao_evidencias",
    "post_liberar",
    "post_presenca",
    "post_travar",
    "update_processo_arquivo",
    "update_revisao_evidencia",
)


@pytest.mark.parametrize("operation_id", OPERATION_IDS)
def test_route_nivel_a_smoke(operation_id, tm_client, openapi_ops):
    meta = openapi_ops[operation_id]
    run_route_smoke(tm_client, meta)
