"""Testes de autorização por filial — Controle de Retrabalhos."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from app.application.security.api_delpi_permissions import (
    CONTROLE_RETRABALHO_VIEW,
    CONTROLE_RETRABALHO_VIEW_FILIAL_SC,
)
from app.interface.http.routes.retrabalho.retrabalho_branch_access import (
    branch_access_error,
    branch_view_allowed,
)


def _as_user(permissions: list[str]):
    user = SimpleNamespace(is_superadmin=False, permissions=permissions)
    return (
        patch(
            "app.interface.http.branch_access_gate.get_current_user",
            return_value=user,
        ),
        patch(
            "app.interface.http.branch_access_gate.has_permission",
            side_effect=lambda current_user, perm: perm in user.permissions,
        ),
    )


def test_branch_view_allowed_with_global_view_permission() -> None:
    user_patch, perm_patch = _as_user([CONTROLE_RETRABALHO_VIEW])
    with user_patch, perm_patch:
        assert branch_view_allowed("01") is True
        assert branch_view_allowed("02") is True


def test_branch_view_allowed_with_filial_sc_only() -> None:
    user_patch, perm_patch = _as_user([CONTROLE_RETRABALHO_VIEW_FILIAL_SC])
    with user_patch, perm_patch:
        assert branch_view_allowed("01") is True
        assert branch_view_allowed("02") is False


def test_sc_only_allows_branch_01_and_denies_consolidated() -> None:
    """Caso P0: Analista SC com view.filial-sc — 01 ok; omitir branch = consolidado 403."""
    user_patch, perm_patch = _as_user([CONTROLE_RETRABALHO_VIEW_FILIAL_SC])
    with user_patch, perm_patch:
        assert branch_access_error("01") is None
        denied = branch_access_error(None)
        assert denied is not None
        assert denied.status_code == 403
        assert b"consolidado" in denied.body


def test_branch_access_error_returns_403_for_denied_filial() -> None:
    with patch(
        "app.interface.http.branch_access_gate.BranchAccessGate.branch_view_allowed",
        return_value=False,
    ):
        response = branch_access_error("02")

    assert response is not None
    assert response.status_code == 403
