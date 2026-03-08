from functools import wraps
from flask import g, jsonify

from .authz_core import has_permission


def require_permission(permission_code: str):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            user = getattr(g, "current_user", None)

            if not user:
                return jsonify({"error": "Unauthorized"}), 401

            user_dict = {
                "permissions": getattr(user, "permissions", []),
                "is_superadmin": getattr(user, "is_superadmin", False),
            }

            if not has_permission(user_dict, permission_code):
                return jsonify({"error": "Forbidden"}), 403

            return func(*args, **kwargs)

        return wrapper

    return decorator