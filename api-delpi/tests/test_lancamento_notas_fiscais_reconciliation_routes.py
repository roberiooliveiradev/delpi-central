"""Smoke HTTP — conciliação LNF (permissão manage)."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.application.security import api_delpi_permissions as perms


def test_run_reconciliation_without_manage_raises_forbidden() -> None:
    from app.interface.http.routes.lancamento_notas_fiscais.lancamento_notas_fiscais_router import (
        run_reconciliation,
    )

    user = SimpleNamespace(
        is_superadmin=False,
        permissions=[perms.LANCAMENTO_NOTAS_FISCAIS_VIEW],
    )
    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=user,
    ):
        with pytest.raises(Exception, match="Forbidden"):
            run_reconciliation(body=None)


def test_run_reconciliation_with_manage_ok() -> None:
    from app.interface.http.routes.lancamento_notas_fiscais.lancamento_notas_fiscais_router import (
        ReconciliationRunBody,
        run_reconciliation,
    )

    user = SimpleNamespace(
        id="u-manage",
        name="Gestor",
        is_superadmin=False,
        permissions=[perms.LANCAMENTO_NOTAS_FISCAIS_MANAGE],
    )
    summary = {
        "examined": 0,
        "matched": 0,
        "posted": 0,
        "not_found": 0,
        "ambiguous": 0,
        "failed": 0,
    }
    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=user,
    ), patch(
        "delpi_auth.request_context.get_current_user",
        return_value=user,
    ), patch(
        "app.interface.http.routes.lancamento_notas_fiscais.lancamento_notas_fiscais_router.build_run_invoice_posting_reconciliation_use_case"
    ) as build_uc:
        build_uc.return_value.execute.return_value = summary
        response = run_reconciliation(body=ReconciliationRunBody(limit=10))

    payload = json.loads(response.body.decode("utf-8"))
    assert payload["success"] is True
    assert payload["data"] == summary
    assert payload["meta"]["operationId"] == (
        "run_lancamento_notas_fiscais_reconciliation"
    )
    build_uc.return_value.execute.assert_called_once()


def test_refresh_reconciliation_without_access_raises_forbidden() -> None:
    from app.interface.http.routes.lancamento_notas_fiscais.lancamento_notas_fiscais_router import (
        refresh_reconciliation,
    )

    user = SimpleNamespace(
        is_superadmin=False,
        permissions=["other.access"],
    )
    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=user,
    ):
        with pytest.raises(Exception, match="Forbidden"):
            refresh_reconciliation()


def test_refresh_reconciliation_with_access_ok_minimal_payload() -> None:
    from app.interface.http.routes.lancamento_notas_fiscais.lancamento_notas_fiscais_router import (
        refresh_reconciliation,
    )

    user = SimpleNamespace(
        id="u-access",
        name="Operador",
        is_superadmin=False,
        permissions=[perms.LANCAMENTO_NOTAS_FISCAIS_ACCESS],
    )
    summary = {"status": "completed", "updated": 2}
    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=user,
    ), patch(
        "delpi_auth.request_context.get_current_user",
        return_value=user,
    ), patch(
        "app.interface.http.routes.lancamento_notas_fiscais.lancamento_notas_fiscais_router.build_refresh_invoice_posting_reconciliation_use_case"
    ) as build_uc:
        build_uc.return_value.execute.return_value = summary
        response = refresh_reconciliation()

    payload = json.loads(response.body.decode("utf-8"))
    assert payload["success"] is True
    assert payload["data"] == summary
    assert set(payload["data"].keys()) == {"status", "updated"}
    assert payload["meta"]["operationId"] == (
        "refresh_lancamento_notas_fiscais_reconciliation"
    )
