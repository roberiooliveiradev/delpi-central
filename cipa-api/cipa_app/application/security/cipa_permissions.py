"""Códigos RBAC do plugin CIPA — alinhados a cipa.manifest.json."""

from __future__ import annotations

from delpi_auth.authz_core import has_permission

UNIT_CODES = ("01", "02")

ACTIONS = (
    "view",
    "create",
    "edit",
    "delete",
    "submit",
    "sign",
    "cancel",
    "finalize",
    "export",
    "manage_signers",
    "view_audit",
    "admin",
)


def permission_code(action: str, unit_code: str) -> str:
    if action == "admin":
        return f"cipa.admin.filial-{unit_code}"
    return f"cipa.minutes.{action}.filial-{unit_code}"


VIEW_FILIAL: dict[str, str] = {code: permission_code("view", code) for code in UNIT_CODES}
CREATE_FILIAL: dict[str, str] = {code: permission_code("create", code) for code in UNIT_CODES}
EDIT_FILIAL: dict[str, str] = {code: permission_code("edit", code) for code in UNIT_CODES}
DELETE_FILIAL: dict[str, str] = {code: permission_code("delete", code) for code in UNIT_CODES}
SUBMIT_FILIAL: dict[str, str] = {code: permission_code("submit", code) for code in UNIT_CODES}
SIGN_FILIAL: dict[str, str] = {code: permission_code("sign", code) for code in UNIT_CODES}
CANCEL_FILIAL: dict[str, str] = {code: permission_code("cancel", code) for code in UNIT_CODES}
FINALIZE_FILIAL: dict[str, str] = {code: permission_code("finalize", code) for code in UNIT_CODES}
EXPORT_FILIAL: dict[str, str] = {code: permission_code("export", code) for code in UNIT_CODES}
MANAGE_SIGNERS_FILIAL: dict[str, str] = {
    code: permission_code("manage_signers", code) for code in UNIT_CODES
}
VIEW_AUDIT_FILIAL: dict[str, str] = {
    code: permission_code("view_audit", code) for code in UNIT_CODES
}
ADMIN_FILIAL: dict[str, str] = {code: permission_code("admin", code) for code in UNIT_CODES}

ACTION_MAPS: dict[str, dict[str, str]] = {
    "view": VIEW_FILIAL,
    "create": CREATE_FILIAL,
    "edit": EDIT_FILIAL,
    "delete": DELETE_FILIAL,
    "submit": SUBMIT_FILIAL,
    "sign": SIGN_FILIAL,
    "cancel": CANCEL_FILIAL,
    "finalize": FINALIZE_FILIAL,
    "export": EXPORT_FILIAL,
    "manage_signers": MANAGE_SIGNERS_FILIAL,
    "view_audit": VIEW_AUDIT_FILIAL,
    "admin": ADMIN_FILIAL,
}


def normalize_unit_code(value: str | None) -> str | None:
    code = (value or "").strip()
    if code in UNIT_CODES:
        return code
    return None


def user_permissions(user) -> list[str]:
    raw = getattr(user, "permissions", None) or getattr(user, "permission_codes", None) or []
    return [str(item) for item in raw]


def has_unit_action(user, action: str, unit_code: str) -> bool:
    code = normalize_unit_code(unit_code)
    if not code:
        return False
    if has_permission(user, ADMIN_FILIAL[code]):
        return True
    mapping = ACTION_MAPS.get(action)
    if not mapping:
        return False
    return has_permission(user, mapping[code])


def unit_codes_for_action(user, action: str) -> list[str]:
    return [code for code in UNIT_CODES if has_unit_action(user, action, code)]


def assert_unit_action(user, action: str, unit_code: str) -> None:
    if not has_unit_action(user, action, unit_code):
        raise PermissionError(
            f"Sem permissão para '{action}' na unidade {unit_code}."
        )
