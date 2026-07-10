from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from app.interface.http.routes.quality.audit_5s_branch_access import (
    branch_access_error,
    branch_audit_allowed,
    branch_view_allowed,
)


def test_branch_view_allowed_for_matching_filial_permission() -> None:
    user = SimpleNamespace(is_superadmin=False)
    with patch(
        "app.interface.http.routes.quality.audit_5s_branch_access.get_current_user",
        return_value=user,
    ), patch(
        "app.interface.http.routes.quality.audit_5s_branch_access.has_permission",
        side_effect=lambda _user, perm: perm == "auditoria-5s.view.filial-01",
    ):
        assert branch_view_allowed("01") is True
        assert branch_view_allowed("02") is False


def test_branch_audit_allowed_for_matching_audit_permission() -> None:
    user = SimpleNamespace(is_superadmin=False)
    with patch(
        "app.interface.http.routes.quality.audit_5s_branch_access.get_current_user",
        return_value=user,
    ), patch(
        "app.interface.http.routes.quality.audit_5s_branch_access.has_permission",
        side_effect=lambda _user, perm: perm == "auditoria-5s.audit.filial-02",
    ):
        assert branch_audit_allowed("02") is True
        assert branch_audit_allowed("01") is False


def test_branch_access_error_returns_403_when_denied() -> None:
    with patch(
        "app.interface.http.routes.quality.audit_5s_branch_access.branch_view_allowed",
        return_value=False,
    ):
        response = branch_access_error("01")
    assert response is not None
    assert response.status_code == 403
