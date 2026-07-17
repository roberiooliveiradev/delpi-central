"""Códigos RBAC do plugin CIPA — alinhados a cipa.manifest.json."""

from __future__ import annotations

from delpi_auth.authz_core import has_permission

UNIT_CODES = ("01", "02")

VIEW_PERMISSION = "cipa.view"
MANAGE_PERMISSION = "cipa.manage"
SIGN_PERMISSION = "cipa.sign"
ADMIN_PERMISSION = "cipa.admin"

UNIT_PERMISSIONS: dict[str, str] = {
    "01": "cipa.unit.filial-01",
    "02": "cipa.unit.filial-02",
}

UNIT_LABELS: dict[str, str] = {
    "01": "Santa Catarina",
    "02": "Espírito Santo",
}

ACTION_PERMISSIONS: dict[str, str] = {
    "view": VIEW_PERMISSION,
    "view_audit": VIEW_PERMISSION,
    "create": MANAGE_PERMISSION,
    "edit": MANAGE_PERMISSION,
    "delete": MANAGE_PERMISSION,
    "submit": MANAGE_PERMISSION,
    "cancel": MANAGE_PERMISSION,
    "finalize": MANAGE_PERMISSION,
    "export": MANAGE_PERMISSION,
    "manage_signers": MANAGE_PERMISSION,
    "sign": SIGN_PERMISSION,
    "admin": ADMIN_PERMISSION,
}


def unit_permission_code(unit_code: str) -> str:
    code = normalize_unit_code(unit_code)
    if not code:
        raise ValueError(f"Unidade inválida: {unit_code!r}")
    return UNIT_PERMISSIONS[code]


def action_permission_code(action: str) -> str | None:
    return ACTION_PERMISSIONS.get(action)


def normalize_unit_code(value: str | None) -> str | None:
    code = (value or "").strip()
    if code in UNIT_CODES:
        return code
    return None


def user_permissions(user) -> list[str]:
    raw = getattr(user, "permissions", None) or getattr(user, "permission_codes", None) or []
    return [str(item) for item in raw]


def _has_global_action(user, action: str) -> bool:
    if has_permission(user, ADMIN_PERMISSION):
        return True
    if action in {"view", "view_audit"}:
        return has_permission(user, VIEW_PERMISSION) or has_permission(user, MANAGE_PERMISSION)
    action_permission = ACTION_PERMISSIONS.get(action)
    if not action_permission:
        return False
    return has_permission(user, action_permission)


def has_unit_access(user, unit_code: str) -> bool:
    code = normalize_unit_code(unit_code)
    if not code:
        return False
    if has_permission(user, ADMIN_PERMISSION):
        return True
    return has_permission(user, UNIT_PERMISSIONS[code])


def has_unit_action(user, action: str, unit_code: str) -> bool:
    code = normalize_unit_code(unit_code)
    if not code:
        return False
    if has_permission(user, ADMIN_PERMISSION):
        return True
    if not has_unit_access(user, code):
        return False
    action_permission = ACTION_PERMISSIONS.get(action)
    if not action_permission:
        return False
    return _has_global_action(user, action)


def has_unit_read_access(user, unit_code: str) -> bool:
    return has_unit_action(user, "view", unit_code) or has_unit_action(user, "create", unit_code)


def unit_codes_for_read(user) -> list[str]:
    return [code for code in UNIT_CODES if has_unit_read_access(user, code)]


def unit_codes_for_action(user, action: str) -> list[str]:
    return [code for code in UNIT_CODES if has_unit_action(user, action, code)]


def assert_unit_action(user, action: str, unit_code: str) -> None:
    if not has_unit_action(user, action, unit_code):
        raise PermissionError(
            f"Sem permissão para '{action}' na unidade {unit_code}."
        )


def assert_global_action(user, action: str) -> None:
    """Gate de ação global (sem escopo de unidade) — ex.: perfil de assinatura."""
    if not _has_global_action(user, action):
        raise PermissionError(f"Sem permissão para '{action}'.")


def build_access_payload(user) -> dict[str, object]:
    """Resumo de escopo para o MFE — espelha o modelo enxuto do manifesto."""
    is_admin = has_permission(user, ADMIN_PERMISSION)
    units: list[dict[str, object]] = []

    for code in UNIT_CODES:
        view = has_unit_read_access(user, code)
        manage = has_unit_action(user, "create", code)
        sign = has_unit_action(user, "sign", code)
        if view or manage or sign:
            units.append(
                {
                    "id": code,
                    "label": UNIT_LABELS[code],
                    "view": view,
                    "manage": manage,
                    "sign": sign,
                }
            )

    return {
        "admin": is_admin,
        "can_view": is_admin or has_permission(user, VIEW_PERMISSION),
        "can_manage": is_admin or has_permission(user, MANAGE_PERMISSION),
        "can_sign": is_admin or has_permission(user, SIGN_PERMISSION),
        "units": units,
    }
