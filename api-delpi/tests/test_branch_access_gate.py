"""Testes — BranchAccessGate."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from app.application.security.api_delpi_permissions import (
    INSPECOES_ENTRADA_BRANCH_VIEW_PERMS,
    INSPECOES_ENTRADA_VIEW,
    INSPECOES_ENTRADA_VIEW_FILIAL_01,
)
from app.interface.http.branch_access_gate import BranchAccessGate

_GATE = BranchAccessGate(
    global_view_perm=INSPECOES_ENTRADA_VIEW,
    branch_view_perms=dict(INSPECOES_ENTRADA_BRANCH_VIEW_PERMS),
    resource_label="inspeções de entrada",
)


def test_gate_todas_requires_consolidated() -> None:
    with patch(
        "app.interface.http.branch_access_gate.BranchAccessGate.consolidated_view_allowed",
        return_value=False,
    ):
        response = _GATE.branch_access_error("Todas")
    assert response is not None
    assert response.status_code == 403


def test_gate_todas_allowed_when_consolidated() -> None:
    with patch(
        "app.interface.http.branch_access_gate.BranchAccessGate.consolidated_view_allowed",
        return_value=True,
    ):
        assert _GATE.branch_access_error("Todas") is None
        assert _GATE.branch_access_error(None) is None
        assert _GATE.branch_access_error("") is None


def test_gate_filial_01_only() -> None:
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
            assert _GATE.branch_view_allowed("01") is True
            assert _GATE.branch_view_allowed("02") is False
            assert _GATE.consolidated_view_allowed() is False
            assert _GATE.branch_access_error("01") is None
            assert _GATE.branch_access_error("02") is not None
