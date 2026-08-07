"""Códigos RBAC do módulo Comercial — capacidades EN + aliases legados (coexistência 5C)."""

from __future__ import annotations

from typing import Any, Iterable

COMMERCIAL_ACCOUNTS_VIEW = "commercial.accounts.view"
COMMERCIAL_WORKLIST_VIEW = "commercial.worklist.view"
COMMERCIAL_FOLLOWUPS_MANAGE = "commercial.followups.manage"
COMMERCIAL_SELLER_PORTFOLIOS_MANAGE = "commercial.seller-portfolios.manage"
COMMERCIAL_AUDIT_VIEW = "commercial.audit.view"
COMMERCIAL_ANALYTICS_VIEW = "commercial.analytics.view"
COMMERCIAL_PROPOSALS_VIEW = "commercial.proposals.view"
COMMERCIAL_PROPOSALS_EXPORT = "commercial.proposals.export"
# Alias PT curto-prazo (manifest 0.3.0 pré-rename) — remover no cleanup-later
COMMERCIAL_PROPOSTAS_VIEW_LEGACY = "commercial.propostas.view"
COMMERCIAL_PROPOSTAS_EXPORT_LEGACY = "commercial.propostas.export"
COMMERCIAL_ACCOUNTS_TEAM_VIEW = "commercial.accounts.team.view"
COMMERCIAL_WORKLIST_TEAM_VIEW = "commercial.worklist.team.view"

PEDIDOS_VENDA_ABERTOS_ACCESS = "pedidos-venda-abertos.access"
PEDIDOS_VENDA_ABERTOS_ADMIN = "pedidos-venda-abertos.admin"
DASHBOARD_COMMERCIAL_VIEW = "dashboard-commercial.view"
PROPOSTAS_COMERCIAIS_VIEW = "propostas-comerciais.view"
API_DELPI_ACCESS = "api-delpi.access"

COMMERCIAL_READ_PERMISSIONS: tuple[str, ...] = (
    COMMERCIAL_ACCOUNTS_VIEW,
    PEDIDOS_VENDA_ABERTOS_ACCESS,
    API_DELPI_ACCESS,
)

COMMERCIAL_WORKLIST_PERMISSIONS: tuple[str, ...] = (
    COMMERCIAL_WORKLIST_VIEW,
    API_DELPI_ACCESS,
)

COMMERCIAL_FOLLOWUPS_PERMISSIONS: tuple[str, ...] = (
    COMMERCIAL_FOLLOWUPS_MANAGE,
    API_DELPI_ACCESS,
)

COMMERCIAL_MANAGE_PERMISSIONS: tuple[str, ...] = (
    COMMERCIAL_SELLER_PORTFOLIOS_MANAGE,
    PEDIDOS_VENDA_ABERTOS_ADMIN,
    API_DELPI_ACCESS,
)

COMMERCIAL_AUDIT_PERMISSIONS: tuple[str, ...] = (
    COMMERCIAL_AUDIT_VIEW,
    COMMERCIAL_SELLER_PORTFOLIOS_MANAGE,
    PEDIDOS_VENDA_ABERTOS_ADMIN,
    API_DELPI_ACCESS,
)

# Gestão BI / OTD / OV — aliases enquanto dashboard-commercial coexiste (G3)
COMMERCIAL_ANALYTICS_PERMISSIONS: tuple[str, ...] = (
    COMMERCIAL_ANALYTICS_VIEW,
    DASHBOARD_COMMERCIAL_VIEW,
    API_DELPI_ACCESS,
)

# Documento ADY + PDF (G3) — canônico EN + alias PT + plugin irmão
COMMERCIAL_PROPOSALS_VIEW_PERMISSIONS: tuple[str, ...] = (
    COMMERCIAL_PROPOSALS_VIEW,
    COMMERCIAL_PROPOSTAS_VIEW_LEGACY,
    PROPOSTAS_COMERCIAIS_VIEW,
    DASHBOARD_COMMERCIAL_VIEW,
    API_DELPI_ACCESS,
)

COMMERCIAL_PROPOSALS_EXPORT_PERMISSIONS: tuple[str, ...] = (
    COMMERCIAL_PROPOSALS_EXPORT,
    COMMERCIAL_PROPOSALS_VIEW,
    COMMERCIAL_PROPOSTAS_EXPORT_LEGACY,
    COMMERCIAL_PROPOSTAS_VIEW_LEGACY,
    PROPOSTAS_COMERCIAIS_VIEW,
    DASHBOARD_COMMERCIAL_VIEW,
    API_DELPI_ACCESS,
)

# Compat: nomes antigos ainda referenciados em testes/rotas até cleanup
COMMERCIAL_PROPOSTAS_VIEW = COMMERCIAL_PROPOSALS_VIEW
COMMERCIAL_PROPOSTAS_EXPORT = COMMERCIAL_PROPOSALS_EXPORT
COMMERCIAL_PROPOSTAS_VIEW_PERMISSIONS = COMMERCIAL_PROPOSALS_VIEW_PERMISSIONS
COMMERCIAL_PROPOSTAS_EXPORT_PERMISSIONS = COMMERCIAL_PROPOSALS_EXPORT_PERMISSIONS

# Team — sem alias PVA (G4). Lista de carteiras = team.view OU manage (+ aliases manage).
COMMERCIAL_ACCOUNTS_TEAM_PERMISSIONS: tuple[str, ...] = (COMMERCIAL_ACCOUNTS_TEAM_VIEW,)

COMMERCIAL_WORKLIST_TEAM_PERMISSIONS: tuple[str, ...] = (COMMERCIAL_WORKLIST_TEAM_VIEW,)

COMMERCIAL_LIST_PORTFOLIOS_PERMISSIONS: tuple[str, ...] = (
    COMMERCIAL_ACCOUNTS_TEAM_VIEW,
    *COMMERCIAL_MANAGE_PERMISSIONS,
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


def can_view_worklist(user: Any | None) -> bool:
    return has_any_permission(user, COMMERCIAL_WORKLIST_PERMISSIONS)


def can_manage_followups(user: Any | None) -> bool:
    return has_any_permission(user, COMMERCIAL_FOLLOWUPS_PERMISSIONS)


def can_manage_portfolios(user: Any | None) -> bool:
    return has_any_permission(user, COMMERCIAL_MANAGE_PERMISSIONS)


def can_view_audit(user: Any | None) -> bool:
    return has_any_permission(user, COMMERCIAL_AUDIT_PERMISSIONS)


def can_view_analytics(user: Any | None) -> bool:
    return has_any_permission(user, COMMERCIAL_ANALYTICS_PERMISSIONS)


def can_view_proposals(user: Any | None) -> bool:
    return has_any_permission(user, COMMERCIAL_PROPOSALS_VIEW_PERMISSIONS)


def can_export_proposals(user: Any | None) -> bool:
    return has_any_permission(user, COMMERCIAL_PROPOSALS_EXPORT_PERMISSIONS)


# Alias PT API
can_view_propostas = can_view_proposals
can_export_propostas = can_export_proposals


def can_view_accounts_team(user: Any | None) -> bool:
    return has_any_permission(user, COMMERCIAL_ACCOUNTS_TEAM_PERMISSIONS)


def can_view_worklist_team(user: Any | None) -> bool:
    return has_any_permission(user, COMMERCIAL_WORKLIST_TEAM_PERMISSIONS)


def can_use_team_scope(user: Any | None) -> bool:
    """Filtro multi-vendedor / Gestão Equipe: team.view OU manage (+ aliases)."""
    return can_view_accounts_team(user) or can_manage_portfolios(user)
