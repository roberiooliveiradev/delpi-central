"""Contratos e permissões — lançamento-notas-fiscais."""

from __future__ import annotations

from app.application.security import api_delpi_permissions as perms
from app.interface.http.route_contract_registry import ROUTE_CONTRACTS

OPERATION_IDS = {
    "search_lancamento_notas_fiscais_suppliers",
    "create_lancamento_notas_fiscais_request",
    "list_lancamento_notas_fiscais_requests",
    "get_lancamento_notas_fiscais_request",
    "update_lancamento_notas_fiscais_request",
    "start_lancamento_notas_fiscais_request",
    "block_lancamento_notas_fiscais_request",
    "resume_lancamento_notas_fiscais_request",
    "add_lancamento_notas_fiscais_comment",
    "cancel_lancamento_notas_fiscais_request",
    "post_manual_lancamento_notas_fiscais_request",
    "run_lancamento_notas_fiscais_reconciliation",
    "refresh_lancamento_notas_fiscais_reconciliation",
}


def test_permission_constants() -> None:
    assert perms.LANCAMENTO_NOTAS_FISCAIS_CREATE == "lancamento-notas-fiscais.create"
    assert perms.LANCAMENTO_NOTAS_FISCAIS_VIEW == "lancamento-notas-fiscais.view"
    assert perms.LANCAMENTO_NOTAS_FISCAIS_PROCESS == "lancamento-notas-fiscais.process"
    assert perms.LANCAMENTO_NOTAS_FISCAIS_MANAGE == "lancamento-notas-fiscais.manage"
    assert perms.LANCAMENTO_NOTAS_FISCAIS_CREATE in perms.LANCAMENTO_NOTAS_FISCAIS_READ_PERMISSIONS
    assert (
        perms.LANCAMENTO_NOTAS_FISCAIS_PROCESS
        in perms.LANCAMENTO_NOTAS_FISCAIS_PROCESS_PERMISSIONS
    )


def test_route_contracts_registered() -> None:
    missing = sorted(OPERATION_IDS - set(ROUTE_CONTRACTS))
    assert not missing, f"operation_id ausente: {missing}"
    assert ROUTE_CONTRACTS["list_lancamento_notas_fiscais_requests"].shape == "paged_list"
    assert ROUTE_CONTRACTS["create_lancamento_notas_fiscais_request"].entity == (
        "invoice_posting_request"
    )
