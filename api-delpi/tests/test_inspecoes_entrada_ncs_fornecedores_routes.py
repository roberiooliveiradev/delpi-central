"""Contrato da consulta de NCs de fornecedores no plugin de recebimento."""

import json
from unittest.mock import MagicMock, patch

from app.domain.services.quality.nonconformity_query_filter_service import (
    qi2_tipo_codes_for_filter,
)


def _body(response):
    return json.loads(response.body.decode("utf-8"))


@patch(
    "app.interface.http.routes.inspecoes_entrada.ncs_fornecedores_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.inspecoes_entrada.ncs_fornecedores_router.build_list_nonconformity_use_case"
)
def test_supplier_ncs_force_supplier_type_and_branch(mock_build, _gate):
    from app.interface.http.routes.inspecoes_entrada.ncs_fornecedores_router import (
        list_inspecoes_entrada_ncs_fornecedores_route,
    )

    result = MagicMock()
    result.to_dict.return_value = {
        "items": [{"branch": "02", "type_code": "3", "code": "NC001"}],
        "page": 1, "page_size": 20, "total": 1, "total_pages": 1,
    }
    use_case = MagicMock()
    use_case.execute.return_value = result
    mock_build.return_value = use_case

    response = list_inspecoes_entrada_ncs_fornecedores_route(
        branch="02", start_date="2026-11-01", end_date="2026-11-08",
        status=None, item_code=None, description=None, page=1, page_size=20,
    )
    body = _body(response)
    assert body["success"] is True
    assert body["meta"]["operationId"] == "list_inspecoes_entrada_ncs_fornecedores"
    assert body["meta"]["shape"] == "paged_list"
    request = use_case.execute.call_args.args[0]
    assert request.type == "supplier"
    assert request.branch == "02"
    assert request.date_start == "2026-11-01"
    assert qi2_tipo_codes_for_filter(request.type) == ["3"]


@patch(
    "app.interface.http.routes.inspecoes_entrada.ncs_fornecedores_router.branch_access_error"
)
@patch(
    "app.interface.http.routes.inspecoes_entrada.ncs_fornecedores_router.build_list_nonconformity_use_case"
)
def test_supplier_ncs_denied_branch_never_reads_totvs(mock_build, gate):
    from app.core.responses import error_response
    from app.interface.http.routes.inspecoes_entrada.ncs_fornecedores_router import (
        list_inspecoes_entrada_ncs_fornecedores_route,
    )
    gate.return_value = error_response("Sem permissão", status_code=403)
    response = list_inspecoes_entrada_ncs_fornecedores_route(
        branch="01", start_date=None, end_date=None,
        status=None, item_code=None, description=None, page=1, page_size=20,
    )
    assert response.status_code == 403
    mock_build.assert_not_called()
