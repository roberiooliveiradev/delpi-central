# shared/delpi_auth/authz_core.py

def has_permission(user, permission_code: str) -> bool:
    if getattr(user, "is_superadmin", False):
        return True

    permissions = getattr(user, "permissions", [])

    return permission_code in permissions


def has_any_permission(user, permission_codes) -> bool:
    if getattr(user, "is_superadmin", False):
        return True

    permissions = getattr(user, "permissions", [])

    return any(code in permissions for code in permission_codes)


def has_all_permissions(user, permission_codes) -> bool:
    if getattr(user, "is_superadmin", False):
        return True

    permissions = getattr(user, "permissions", [])

    return all(code in permissions for code in permission_codes)