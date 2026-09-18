"""Canonical Supplies RBAC. Core is the authority; this module only names codes."""

from __future__ import annotations

from app.domain.entities import EffectiveUser

SUPPLIES_ACCESS = "supplies.access"
SUPPLIES_MANAGE = "supplies.manage"
SUPPLIES_VIEW_ALL = "supplies.purchase-requests.view-all"
UNIT_PREFIX = "supplies.unit.filial-"


def _has(user: EffectiveUser, code: str) -> bool:
    return user.has_permission(code)


def has_canonical_access(user: EffectiveUser) -> bool:
    return _has(user, SUPPLIES_ACCESS)


def has_canonical_manage(user: EffectiveUser) -> bool:
    return _has(user, SUPPLIES_MANAGE)


def can_enter_shell(user: EffectiveUser) -> bool:
    return has_canonical_access(user) or has_canonical_manage(user)


def can_use_portal(user: EffectiveUser) -> bool:
    return has_canonical_access(user)


def can_use_analytics(user: EffectiveUser) -> bool:
    return has_canonical_access(user)


def can_use_operations(user: EffectiveUser) -> bool:
    return has_canonical_access(user)


def can_use_purchase_requests(user: EffectiveUser) -> bool:
    return has_canonical_access(user)


def can_administer(user: EffectiveUser) -> bool:
    return has_canonical_manage(user)


def can_view_all_purchase_requests(user: EffectiveUser) -> bool:
    return _has(user, SUPPLIES_VIEW_ALL)


def can_export_purchase_requests(user: EffectiveUser) -> bool:
    return has_canonical_access(user)
