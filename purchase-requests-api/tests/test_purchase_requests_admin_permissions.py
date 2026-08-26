from __future__ import annotations

from types import SimpleNamespace

from purchase_requests_app.application.security.purchase_requests_permissions import (
    ADMIN_PERMISSION,
    RBAC_MANAGE_PERMISSION,
    has_admin,
)


def test_has_admin_superadmin() -> None:
    user = SimpleNamespace(is_superadmin=True, permissions=[])
    assert has_admin(user)


def test_has_admin_module_permission() -> None:
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=[ADMIN_PERMISSION, "purchase-requests.access"],
    )
    assert has_admin(user)


def test_has_admin_rbac_manage() -> None:
    user = SimpleNamespace(is_superadmin=False, permissions=[RBAC_MANAGE_PERMISSION])
    assert has_admin(user)


def test_has_admin_denied_without_permissions() -> None:
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=["purchase-requests.access", "purchase-requests.unit.filial-01"],
    )
    assert not has_admin(user)
