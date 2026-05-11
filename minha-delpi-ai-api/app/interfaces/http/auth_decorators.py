from functools import wraps

from flask import g

from app.domain.exceptions.auth_exceptions import AuthenticationError


def require_auth():
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not getattr(g, "current_user", None):
                raise AuthenticationError("Authentication required")

            return fn(*args, **kwargs)

        return wrapper

    return decorator
