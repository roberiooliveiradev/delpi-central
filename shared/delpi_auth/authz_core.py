# shared/delpi_auth/athz_core.py

def has_permission(user: dict, permission_code: str) -> bool:

    if not user:
        return False

    if user.get("is_superadmin"):
        return True

    permissions = user.get("permissions") or []

    return permission_code in permissions


def has_any_permission(user: dict, permissions: list[str]) -> bool:

    if not user:
        return False

    if user.get("is_superadmin"):
        return True

    user_permissions = set(user.get("permissions") or [])

    return any(p in user_permissions for p in permissions)


def has_all_permissions(user: dict, permissions: list[str]) -> bool:

    if not user:
        return False

    if user.get("is_superadmin"):
        return True

    user_permissions = set(user.get("permissions") or [])

    return all(p in user_permissions for p in permissions)