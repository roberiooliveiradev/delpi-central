from __future__ import annotations

from functools import wraps

from flask import g, request

from app.application.services.authorization_service import AuthorizationService
from app.domain.exceptions import AuthenticationError, AuthorizationError


def require_auth():
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not getattr(g, "current_user", None):
                raise AuthenticationError("Unauthorized")
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def require_permission(permission: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = getattr(g, "current_user", None)
            if not user:
                raise AuthenticationError("Unauthorized")
            AuthorizationService().require_permission(user, permission)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def require_unit(branch_arg: str = "branch"):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = getattr(g, "current_user", None)
            if not user:
                raise AuthenticationError("Unauthorized")

            branch = kwargs.get(branch_arg)
            if branch is None and request.view_args:
                branch = request.view_args.get(branch_arg)
            if branch is None:
                branch = request.args.get(branch_arg)
            if not branch:
                raise AuthorizationError("Forbidden")

            AuthorizationService().require_unit(user, str(branch))
            return fn(*args, **kwargs)

        return wrapper

    return decorator
