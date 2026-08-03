"""Testes de autorização por filial — Inspeções de Entrada."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from app.application.security.api_delpi_permissions import (
    INSPECOES_ENTRADA_VIEW,
    INSPECOES_ENTRADA_VIEW_FILIAL_01,
)
from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_branch_access import (
    branch_access_error,
    branch_view_allowed,
)


def test_branch_view_allowed_with_global_view_permission() -> None:
    user = SimpleNamespace(is_superadmin=False, permissions=[INSPECOES_ENTRADA_VIEW])

    with patch(
        "app.interface.http.branch_access_gate.get_current_user",
        return_value=user,
    ):
        with patch(
            "app.interface.http.branch_access_gate.has_permission",
            side_effect=lambda current_user, perm: perm in user.permissions,
        ):
            assert branch_view_allowed("01") is True
            assert branch_view_allowed("02") is True


def test_branch_view_allowed_with_filial_01_only() -> None:
    user = SimpleNamespace(
        is_superadmin=False, permissions=[INSPECOES_ENTRADA_VIEW_FILIAL_01]
    )

    with patch(
        "app.interface.http.branch_access_gate.get_current_user",
        return_value=user,
    ):
        with patch(
            "app.interface.http.branch_access_gate.has_permission",
            side_effect=lambda current_user, perm: perm in user.permissions,
        ):
            assert branch_view_allowed("01") is True
            assert branch_view_allowed("02") is False


def test_branch_access_error_returns_403_for_denied_filial() -> None:
    with patch(
        "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_branch_access.branch_view_allowed",
        return_value=False,
    ):
        # gate uses its own method — patch on Gate instance via consolidated path
        with patch(
            "app.interface.http.branch_access_gate.BranchAccessGate.branch_view_allowed",
            return_value=False,
        ):
            response = branch_access_error("02")

    assert response is not None
    assert response.status_code == 403


def test_branch_access_error_todas_requires_consolidated() -> None:
    with patch(
        "app.interface.http.branch_access_gate.BranchAccessGate.consolidated_view_allowed",
        return_value=False,
    ):
        response = branch_access_error("all")

    assert response is not None
    assert response.status_code == 403


def test_branch_access_error_todas_allowed() -> None:
    with patch(
        "app.interface.http.branch_access_gate.BranchAccessGate.consolidated_view_allowed",
        return_value=True,
    ):
        assert branch_access_error("all") is None
        assert branch_access_error(None) is None
