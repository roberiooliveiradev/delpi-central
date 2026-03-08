from functools import wraps
from flask import g, jsonify

from .policy_engine import evaluate_policy


def policy(name: str):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            user_obj = getattr(g, "current_user", None)

            if not user_obj:
                return jsonify({"error": "Unauthorized"}), 401

            user = {
                "permissions": getattr(user_obj, "permissions", []),
                "is_superadmin": getattr(user_obj, "is_superadmin", False),
            }

            if user["is_superadmin"]:
                return func(*args, **kwargs)

            allowed = evaluate_policy(name, user, **kwargs)

            if not allowed:
                return jsonify({"error": "Forbidden"}), 403

            return func(*args, **kwargs)

        return wrapper

    return decorator