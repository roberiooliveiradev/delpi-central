"""Códigos RBAC do Customer Experience — alinhados a customer-experience.manifest.json."""

from __future__ import annotations

from typing import Any

from delpi_auth.authz_core import has_permission

CX_ACCESS = "customer-experience.access"
CX_ADMIN = "customer-experience.admin"

CX_PARTICIPANTS_READ = "customer-experience.participants.read"
CX_PARTICIPANTS_WRITE = "customer-experience.participants.write"
CX_PARTICIPANTS_MANAGE = "customer-experience.participants.manage"

CX_FORMS_READ = "customer-experience.forms.read"
CX_FORMS_WRITE = "customer-experience.forms.write"
CX_FORMS_MANAGE = "customer-experience.forms.manage"


def _is_superadmin(user: Any | None) -> bool:
    return bool(user is not None and getattr(user, "is_superadmin", False))


def can(user: Any | None, permission: str) -> bool:
    if user is None:
        return False
    if _is_superadmin(user):
        return True
    if has_permission(user, CX_ADMIN):
        return True
    return has_permission(user, permission)


def assert_permission(user: Any | None, permission: str) -> None:
    if not can(user, permission):
        raise PermissionError("Você não tem permissão para esta ação.")
