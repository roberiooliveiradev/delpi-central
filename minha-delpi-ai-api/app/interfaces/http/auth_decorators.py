from functools import wraps

from flask import g

from app.domain.exceptions.auth_exceptions import AuthenticationError
from app.infrastructure.gateways.core_api_http_gateway import CoreApiHttpGateway
from app.application.services.permission_context_service import PermissionContextService


def require_auth():
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not getattr(g, "current_user", None):
                raise AuthenticationError("Authentication required")

            return fn(*args, **kwargs)

        return wrapper

    return decorator


def require_permission(permission: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not getattr(g, "current_user", None):
                raise AuthenticationError("Authentication required")

            access_token = getattr(g, "access_token", None)

            if not access_token:
                raise AuthenticationError("Authentication required")

            permission_service = PermissionContextService(CoreApiHttpGateway())
            g.permission_context = permission_service.require_permission(
                access_token=access_token,
                permission=permission,
            )

            return fn(*args, **kwargs)

        return wrapper

    return decorator
