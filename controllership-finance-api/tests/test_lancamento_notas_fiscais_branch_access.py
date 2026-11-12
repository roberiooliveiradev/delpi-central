"""Testes de autorização por filial — Lançamento de Notas Fiscais."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from controllership_finance_app.application.invoice_posting.permissions import (
    LANCAMENTO_NOTAS_FISCAIS_PROCESS,
    LANCAMENTO_NOTAS_FISCAIS_VIEW,
    LANCAMENTO_NOTAS_FISCAIS_VIEW_FILIAL_01,
)
from controllership_finance_app.interface.http.routes.invoice_posting.branch_access import (
    branch_access_error,
    branch_view_allowed,
    has_global_branch_access,
)

_MOD = "controllership_finance_app.interface.http.routes.invoice_posting.branch_access"


def _patch_user(user: SimpleNamespace):
    return (
        patch(f"{_MOD}.get_current_user", return_value=user),
        patch(
            f"{_MOD}.has_permission",
            side_effect=lambda _current_user, perm: perm in user.permissions,
        ),
    )


def test_global_view_allows_both_branches() -> None:
    user = SimpleNamespace(
        is_superadmin=False, permissions=[LANCAMENTO_NOTAS_FISCAIS_VIEW]
    )
    get_user, has_perm = _patch_user(user)
    with get_user, has_perm:
        assert has_global_branch_access() is True
        assert branch_view_allowed("01") is True
        assert branch_view_allowed("02") is True


def test_process_allows_both_branches() -> None:
    user = SimpleNamespace(
        is_superadmin=False, permissions=[LANCAMENTO_NOTAS_FISCAIS_PROCESS]
    )
    get_user, has_perm = _patch_user(user)
    with get_user, has_perm:
        assert branch_view_allowed("02") is True


def test_filial_01_only() -> None:
    user = SimpleNamespace(
        is_superadmin=False, permissions=[LANCAMENTO_NOTAS_FISCAIS_VIEW_FILIAL_01]
    )
    get_user, has_perm = _patch_user(user)
    with get_user, has_perm:
        assert has_global_branch_access() is False
        assert branch_view_allowed("01") is True
        assert branch_view_allowed("02") is False
        err = branch_access_error("02")
        assert err is not None
        assert err.status_code == 403


def test_superadmin_allows_all() -> None:
    user = SimpleNamespace(is_superadmin=True, permissions=[])
    get_user, has_perm = _patch_user(user)
    with get_user, has_perm:
        assert branch_view_allowed("01") is True
        assert branch_access_error("02") is None
