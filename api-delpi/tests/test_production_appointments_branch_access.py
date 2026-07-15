"""Testes de autorização por filial — Apontamento de Produção."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from app.application.security.api_delpi_permissions import (
    PRODUCTION_APPOINTMENTS_VIEW,
    PRODUCTION_APPOINTMENTS_VIEW_FILIAL_SC,
)
from app.interface.http.routes.production_appointments.production_appointments_branch_access import (
    branch_access_error,
    branch_view_allowed,
)


def test_branch_view_allowed_with_global_view_permission() -> None:
    user = SimpleNamespace(
        is_superadmin=False, permissions=[PRODUCTION_APPOINTMENTS_VIEW]
    )

    with patch(
        "app.interface.http.routes.production_appointments.production_appointments_branch_access.get_current_user",
        return_value=user,
    ):
        with patch(
            "app.interface.http.routes.production_appointments.production_appointments_branch_access.has_permission",
            side_effect=lambda current_user, perm: perm in user.permissions,
        ):
            assert branch_view_allowed("01") is True
            assert branch_view_allowed("02") is True


def test_branch_view_allowed_with_filial_sc_only() -> None:
    user = SimpleNamespace(
        is_superadmin=False, permissions=[PRODUCTION_APPOINTMENTS_VIEW_FILIAL_SC]
    )

    with patch(
        "app.interface.http.routes.production_appointments.production_appointments_branch_access.get_current_user",
        return_value=user,
    ):
        with patch(
            "app.interface.http.routes.production_appointments.production_appointments_branch_access.has_permission",
            side_effect=lambda current_user, perm: perm in user.permissions,
        ):
            assert branch_view_allowed("01") is True
            assert branch_view_allowed("02") is False


def test_branch_access_error_returns_403() -> None:
    user = SimpleNamespace(
        is_superadmin=False, permissions=[PRODUCTION_APPOINTMENTS_VIEW_FILIAL_SC]
    )

    with patch(
        "app.interface.http.routes.production_appointments.production_appointments_branch_access.get_current_user",
        return_value=user,
    ):
        with patch(
            "app.interface.http.routes.production_appointments.production_appointments_branch_access.has_permission",
            side_effect=lambda current_user, perm: perm in user.permissions,
        ):
            err = branch_access_error("02")
            assert err is not None
            assert err.status_code == 403
