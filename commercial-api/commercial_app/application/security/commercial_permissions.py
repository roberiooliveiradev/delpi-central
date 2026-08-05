"""Códigos RBAC do módulo Comercial — com aliases legados pedidos-venda-abertos."""

from __future__ import annotations

from typing import Any, Iterable

COMMERCIAL_ACCOUNTS_VIEW = "commercial.accounts.view"
COMMERCIAL_SELLER_PORTFOLIOS_MANAGE = "commercial.seller-portfolios.manage"

PEDIDOS_VENDA_ABERTOS_ACCESS = "pedidos-venda-abertos.access"
PEDIDOS_VENDA_ABERTOS_ADMIN = "pedidos-venda-abertos.admin"
API_DELPI_ACCESS = "api-delpi.access"

COMMERCIAL_READ_PERMISSIONS: tuple[str, ...] = (
    COMMERCIAL_ACCOUNTS_VIEW,
    PEDIDOS_VENDA_ABERTOS_ACCESS,
    API_DELPI_ACCESS,
)

COMMERCIAL_MANAGE_PERMISSIONS: tuple[str, ...] = (
    COMMERCIAL_SELLER_PORTFOLIOS_MANAGE,
    PEDIDOS_VENDA_ABERTOS_ADMIN,
    API_DELPI_ACCESS,
)


def _effective_codes(user: Any | None) -> set[str]:
    if user is None:
        return set()
    codes: set[str] = set()
    permissions = getattr(user, "permissions", None) or []
    roles = getattr(user, "roles", None) or []
    codes.update(str(item) for item in permissions if item)
    codes.update(str(item) for item in roles if item)

    realm_access = getattr(user, "realm_access", None)
    if isinstance(realm_access, dict):
        codes.update(str(item) for item in realm_access.get("roles", []) if item)

    resource_access = getattr(user, "resource_access", None)
    if isinstance(resource_access, dict):
        for client_roles in resource_access.values():
            if isinstance(client_roles, dict):
                codes.update(str(item) for item in client_roles.get("roles", []) if item)

    return codes


def has_any_permission(user: Any | None, permission_codes: Iterable[str]) -> bool:
    if user is None:
        return False
    if getattr(user, "is_superadmin", False):
        return True
    effective = _effective_codes(user)
    return any(code in effective for code in permission_codes)


def can_read_commercial(user: Any | None) -> bool:
    return has_any_permission(user, COMMERCIAL_READ_PERMISSIONS)


def can_manage_portfolios(user: Any | None) -> bool:
    return has_any_permission(user, COMMERCIAL_MANAGE_PERMISSIONS)
