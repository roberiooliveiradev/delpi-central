"""Códigos RBAC do plugin Comitê de Ética e Conduta — alinhados ao manifesto."""

from __future__ import annotations

from delpi_auth.authz_core import has_permission

# Comitê único corporativo (sem filial SC/ES).
CORPORATE_UNIT_CODE = "00"
UNIT_CODES = (CORPORATE_UNIT_CODE,)

VIEW_PERMISSION = "comite-etica-conduta.view"
MANAGE_PERMISSION = "comite-etica-conduta.manage"
SIGN_PERMISSION = "comite-etica-conduta.sign"

ACTION_PERMISSIONS: dict[str, str] = {
    "view": VIEW_PERMISSION,
    "view_audit": VIEW_PERMISSION,
    "create": MANAGE_PERMISSION,
    "edit": MANAGE_PERMISSION,
    "delete": MANAGE_PERMISSION,
    "submit": MANAGE_PERMISSION,
    "cancel": MANAGE_PERMISSION,
    "finalize": MANAGE_PERMISSION,
    "export": VIEW_PERMISSION,
    "manage_signers": MANAGE_PERMISSION,
    "manage_members": MANAGE_PERMISSION,
    "sign": SIGN_PERMISSION,
}


def require_permission(user, action: str) -> None:
    code = ACTION_PERMISSIONS.get(action)
    if not code:
        raise PermissionError(f"Ação desconhecida: {action}")
    if not has_permission(user, code):
        raise PermissionError(f"Sem permissão: {code}")


def can(user, action: str) -> bool:
    code = ACTION_PERMISSIONS.get(action)
    if not code:
        return False
    return bool(has_permission(user, code))


def require_view(user) -> None:
    if not (can(user, "view") or can(user, "create")):
        raise PermissionError(f"Sem permissão: {VIEW_PERMISSION}")


def require_manage(user) -> None:
    require_permission(user, "create")


def require_sign(user) -> None:
    require_permission(user, "sign")


def assert_global_action(user, action: str) -> None:
    """Ações sem escopo de filial (ex.: perfil de assinatura pessoal)."""
    require_permission(user, action)


def has_unit_action(user, action: str, unit_code: str | None = None) -> bool:
    _ = unit_code
    return can(user, action)


def action_permission_code(action: str) -> str | None:
    return ACTION_PERMISSIONS.get(action)


def normalize_unit_code(unit_code: str | None = None) -> str:
    _ = unit_code
    return CORPORATE_UNIT_CODE


def assert_unit_access(user, unit_code: str | None = None) -> str:
    require_view(user)
    return normalize_unit_code(unit_code)


def assert_unit_action(user, action: str, unit_code: str | None = None) -> str:
    require_permission(user, action)
    return normalize_unit_code(unit_code)


def unit_codes_for_read(user) -> list[str]:
    require_view(user)
    return [CORPORATE_UNIT_CODE]


def unit_codes_for_action(user, action: str) -> list[str]:
    require_permission(user, action)
    return [CORPORATE_UNIT_CODE]


def has_unit_read_access(user, unit_code: str | None = None) -> bool:
    _ = unit_code
    return can(user, "view") or can(user, "create")


def build_access_payload(user) -> dict:
    admin = False
    can_view = can(user, "view") or can(user, "create")
    can_manage = can(user, "create")
    can_sign = can(user, "sign") or can_manage
    return {
        "admin": admin,
        "can_view": can_view,
        "can_manage": can_manage,
        "can_sign": can_sign,
        "units": [
            {
                "id": CORPORATE_UNIT_CODE,
                "label": "Comitê de Ética e Conduta",
                "view": can_view,
                "manage": can_manage,
                "sign": can_sign,
            }
        ]
        if can_view or can_manage or can_sign
        else [],
    }
