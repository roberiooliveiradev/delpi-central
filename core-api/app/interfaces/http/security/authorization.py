# app/interfaces/http/security/authorization.py

from functools import wraps
from flask import g

from app.interfaces.http.utils.errors import unauthorized, forbidden


def _get_current_user():
    return getattr(g, "current_user", None)


def require_superadmin():
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = _get_current_user()
            if not user:
                return unauthorized()

            if not getattr(user, "is_superadmin", False):
                return forbidden("Superadmin required")

            return fn(*args, **kwargs)

        return wrapper
    return decorator


def require_permission(permission_code: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = _get_current_user()
            if not user:
                return unauthorized()

            # Bypass para superadmin
            if getattr(user, "is_superadmin", False):
                return fn(*args, **kwargs)

            user_permissions = getattr(user, "permissions", [])

            if permission_code not in user_permissions:
                return forbidden("Permission denied")

            return fn(*args, **kwargs)

        return wrapper
    return decorator


def require_any_permission(permission_codes: list[str]):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = _get_current_user()
            if not user:
                return unauthorized()

            if getattr(user, "is_superadmin", False):
                return fn(*args, **kwargs)

            user_permissions = set(getattr(user, "permissions", []))

            if not any(code in user_permissions for code in permission_codes):
                return forbidden("Permission denied")

            return fn(*args, **kwargs)

        return wrapper
    return decorator