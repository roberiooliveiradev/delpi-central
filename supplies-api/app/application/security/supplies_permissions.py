"""Canonical Supplies RBAC codes and coexistence policies.

Old functional codes stay as surface-scoped compatibility.
They must not alias into global ``supplies.access``.
"""

from __future__ import annotations

from app.domain.entities import EffectiveUser

SUPPLIES_ACCESS = "supplies.access"
SUPPLIES_MANAGE = "supplies.manage"

SUPPLIES_PORTAL_ACCESS = "supplies.portal.access"
SUPPLIES_PURCHASE_REQUESTS_ACCESS = "supplies.purchase-requests.access"
SUPPLIES_OPERATIONS_ACCESS = "supplies.operations.access"
SUPPLIES_ANALYTICS_ACCESS = "supplies.analytics.access"
SUPPLIES_ADMINISTRATION_MANAGE = "supplies.administration.manage"
SUPPLIES_VIEW_ALL = "supplies.purchase-requests.view-all"
SUPPLIES_EXPORT = "supplies.purchase-requests.export"
UNIT_PREFIX = "supplies.unit.filial-"

# Deprecated compatibility — exit when Core grants and consumers are zero.
DEPRECATED_COMPATIBILITY = (
    SUPPLIES_PORTAL_ACCESS,
    SUPPLIES_PURCHASE_REQUESTS_ACCESS,
    SUPPLIES_OPERATIONS_ACCESS,
    SUPPLIES_ANALYTICS_ACCESS,
    SUPPLIES_ADMINISTRATION_MANAGE,
    SUPPLIES_EXPORT,
)


def _has(user: EffectiveUser, code: str) -> bool:
    return user.has_permission(code)


def has_canonical_access(user: EffectiveUser) -> bool:
    return _has(user, SUPPLIES_ACCESS)


def has_canonical_manage(user: EffectiveUser) -> bool:
    return _has(user, SUPPLIES_MANAGE)


def can_enter_shell(user: EffectiveUser) -> bool:
    """Home/help/prefs/capabilities. Manage-only may enter to reach Administração."""
    return (
        has_canonical_access(user)
        or has_canonical_manage(user)
        or _has(user, SUPPLIES_PORTAL_ACCESS)
        or _has(user, SUPPLIES_ANALYTICS_ACCESS)
        or _has(user, SUPPLIES_OPERATIONS_ACCESS)
        or _has(user, SUPPLIES_PURCHASE_REQUESTS_ACCESS)
        or _has(user, SUPPLIES_ADMINISTRATION_MANAGE)
        or _has(user, "dashboard-supplies.view")
        or _has(user, "idd-suprimentos.access")
        or _has(user, "estoque-seguranca.access")
        or _has(user, "purchase-requests.access")
        or _has(user, "purchase-requests.admin")
    )


def can_use_portal(user: EffectiveUser) -> bool:
    return has_canonical_access(user) or _has(user, SUPPLIES_PORTAL_ACCESS)


def can_use_analytics(user: EffectiveUser) -> bool:
    return (
        has_canonical_access(user)
        or _has(user, SUPPLIES_ANALYTICS_ACCESS)
        or _has(user, "dashboard-supplies.view")
        or _has(user, "idd-suprimentos.access")
    )


def can_use_operations(user: EffectiveUser) -> bool:
    return (
        has_canonical_access(user)
        or _has(user, SUPPLIES_OPERATIONS_ACCESS)
        or _has(user, "estoque-seguranca.access")
    )


def can_use_purchase_requests(user: EffectiveUser) -> bool:
    return (
        has_canonical_access(user)
        or _has(user, SUPPLIES_PURCHASE_REQUESTS_ACCESS)
        or _has(user, "purchase-requests.access")
    )


def can_administer(user: EffectiveUser) -> bool:
    return (
        has_canonical_manage(user)
        or _has(user, SUPPLIES_ADMINISTRATION_MANAGE)
        or _has(user, "purchase-requests.admin")
    )


def can_view_all_purchase_requests(user: EffectiveUser) -> bool:
    return _has(user, SUPPLIES_VIEW_ALL) or _has(user, "purchase-requests.view-all")


def can_export_purchase_requests(user: EffectiveUser) -> bool:
    """Canonical access absorbs export. Legacy export requires the SC surface too."""
    if has_canonical_access(user):
        return True
    return can_use_purchase_requests(user) and (
        _has(user, SUPPLIES_EXPORT) or _has(user, "purchase-requests.export")
    )
