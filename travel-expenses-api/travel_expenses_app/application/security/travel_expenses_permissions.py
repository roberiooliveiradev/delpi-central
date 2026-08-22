"""RBAC codes for travel-expenses — aligned with travel-expenses.manifest.json."""

from __future__ import annotations

from delpi_auth.authz_core import has_permission

UNIT_CODES = ("01", "02")

VIEW_PERMISSION = "travel-expenses.view"
WRITE_PERMISSION = "travel-expenses.write"
MANAGE_PERMISSION = "travel-expenses.manage"
ADMIN_PERMISSION = "travel-expenses.admin"

UNIT_PERMISSIONS: dict[str, str] = {
    "01": "travel-expenses.unit.filial-01",
    "02": "travel-expenses.unit.filial-02",
}

UNIT_LABELS: dict[str, str] = {
    "01": "Santa Catarina",
    "02": "Espírito Santo",
}

ACTION_PERMISSIONS: dict[str, str] = {
    "view": VIEW_PERMISSION,
    "write": WRITE_PERMISSION,
    "manage": MANAGE_PERMISSION,
    "admin": ADMIN_PERMISSION,
}


def normalize_unit_code(value: str | None) -> str | None:
    code = (value or "").strip()
    if code in UNIT_CODES:
        return code
    return None


def user_permissions(user) -> list[str]:
    raw = getattr(user, "permissions", None) or getattr(user, "permission_codes", None) or []
    return [str(item) for item in raw]


def is_admin(user) -> bool:
    return has_permission(user, ADMIN_PERMISSION)


def has_unit_access(user, unit_code: str) -> bool:
    code = normalize_unit_code(unit_code)
    if not code:
        return False
    if is_admin(user):
        return True
    return has_permission(user, UNIT_PERMISSIONS[code])


def _has_global_action(user, action: str) -> bool:
    if is_admin(user):
        return True
    if action == "view":
        return (
            has_permission(user, VIEW_PERMISSION)
            or has_permission(user, WRITE_PERMISSION)
            or has_permission(user, MANAGE_PERMISSION)
        )
    if action == "write":
        return has_permission(user, WRITE_PERMISSION) or has_permission(user, MANAGE_PERMISSION)
    if action == "manage":
        return has_permission(user, MANAGE_PERMISSION)
    action_permission = ACTION_PERMISSIONS.get(action)
    if not action_permission:
        return False
    return has_permission(user, action_permission)


def has_unit_action(user, action: str, unit_code: str) -> bool:
    code = normalize_unit_code(unit_code)
    if not code:
        return False
    if is_admin(user):
        return True
    if not has_unit_access(user, code):
        return False
    return _has_global_action(user, action)


def unit_codes_for_action(user, action: str) -> list[str]:
    return [code for code in UNIT_CODES if has_unit_action(user, action, code)]


def unit_codes_for_read(user) -> list[str]:
    return unit_codes_for_action(user, "view")


def assert_unit_action(user, action: str, unit_code: str) -> None:
    if not has_unit_action(user, action, unit_code):
        raise PermissionError(f"Sem permissão para '{action}' na unidade {unit_code}.")


def can_view_all_in_unit(user, unit_code: str) -> bool:
    return has_unit_action(user, "manage", unit_code) or is_admin(user)


def build_access_payload(user) -> dict[str, object]:
    admin = is_admin(user)
    units: list[dict[str, object]] = []
    for code in UNIT_CODES:
        view = has_unit_action(user, "view", code)
        write = has_unit_action(user, "write", code)
        manage = has_unit_action(user, "manage", code)
        if view or write or manage:
            units.append(
                {
                    "id": code,
                    "label": UNIT_LABELS[code],
                    "view": view,
                    "write": write,
                    "manage": manage,
                }
            )
    return {
        "admin": admin,
        "canView": admin or has_permission(user, VIEW_PERMISSION) or has_permission(user, WRITE_PERMISSION),
        "canWrite": admin or has_permission(user, WRITE_PERMISSION) or has_permission(user, MANAGE_PERMISSION),
        "canManage": admin or has_permission(user, MANAGE_PERMISSION),
        "units": units,
    }
