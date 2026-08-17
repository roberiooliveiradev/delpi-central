"""Códigos RBAC do módulo Comercial — catálogo condensado (3 codes)."""

from __future__ import annotations

from typing import Any, Iterable

COMMERCIAL_ACCESS = "commercial.access"
COMMERCIAL_MANAGE = "commercial.manage"
COMMERCIAL_BILLING_NOTIFY = "commercial.billing.notify"

COMMERCIAL_ACCESS_PERMISSIONS: tuple[str, ...] = (COMMERCIAL_ACCESS,)
COMMERCIAL_MANAGE_PERMISSIONS: tuple[str, ...] = (COMMERCIAL_MANAGE,)
COMMERCIAL_BILLING_NOTIFY_PERMISSIONS: tuple[str, ...] = (COMMERCIAL_BILLING_NOTIFY,)

# Aliases de decorator (mesmo conteúdo — sem codes legados).
COMMERCIAL_READ_PERMISSIONS = COMMERCIAL_ACCESS_PERMISSIONS
COMMERCIAL_WORKLIST_PERMISSIONS = COMMERCIAL_ACCESS_PERMISSIONS
COMMERCIAL_FOLLOWUPS_PERMISSIONS = COMMERCIAL_ACCESS_PERMISSIONS
COMMERCIAL_ANALYTICS_PERMISSIONS = COMMERCIAL_ACCESS_PERMISSIONS
COMMERCIAL_PROPOSALS_VIEW_PERMISSIONS = COMMERCIAL_ACCESS_PERMISSIONS
COMMERCIAL_PROPOSALS_EXPORT_PERMISSIONS = COMMERCIAL_ACCESS_PERMISSIONS
COMMERCIAL_AUDIT_PERMISSIONS = COMMERCIAL_ACCESS_PERMISSIONS
COMMERCIAL_PORTFOLIO_BILLING_SHARE_PERMISSIONS = COMMERCIAL_MANAGE_PERMISSIONS
COMMERCIAL_ACCOUNTS_TEAM_PERMISSIONS = COMMERCIAL_MANAGE_PERMISSIONS
COMMERCIAL_WORKLIST_TEAM_PERMISSIONS = COMMERCIAL_MANAGE_PERMISSIONS
COMMERCIAL_LIST_PORTFOLIOS_PERMISSIONS = COMMERCIAL_MANAGE_PERMISSIONS


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


def has_access(user: Any | None) -> bool:
    """Funcionalidades do produto (portal)."""
    return has_any_permission(user, COMMERCIAL_ACCESS_PERMISSIONS)


def has_manage(user: Any | None) -> bool:
    """Administração + escopo irrestrito (todas as carteiras)."""
    return has_any_permission(user, COMMERCIAL_MANAGE_PERMISSIONS)


def has_billing_notify(user: Any | None) -> bool:
    """Destinatário da notificação «Pronto para faturar»."""
    return has_any_permission(user, COMMERCIAL_BILLING_NOTIFY_PERMISSIONS)


# --- Helpers de rota (derivados dos 3 codes; nomes estáveis para callers) ---


def can_read_commercial(user: Any | None) -> bool:
    return has_access(user)


def can_view_worklist(user: Any | None) -> bool:
    return has_access(user)


def can_manage_followups(user: Any | None) -> bool:
    return has_access(user)


def can_manage_portfolios(user: Any | None) -> bool:
    return has_manage(user)


def can_view_audit(user: Any | None) -> bool:
    return has_access(user) or has_manage(user)


def can_view_analytics(user: Any | None) -> bool:
    return has_access(user)


def can_view_portfolio_billing_share(user: Any | None) -> bool:
    """Share empresa / ranking consolidado — só manage (vê todas as carteiras)."""
    return has_manage(user)


def can_view_proposals(user: Any | None) -> bool:
    return has_access(user)


def can_export_proposals(user: Any | None) -> bool:
    return has_access(user)


def can_view_accounts_team(user: Any | None) -> bool:
    return has_manage(user)


def can_view_worklist_team(user: Any | None) -> bool:
    return has_manage(user)


def can_use_team_scope(user: Any | None) -> bool:
    """Filtro multi-vendedor / todas as carteiras = manage."""
    return has_manage(user)
