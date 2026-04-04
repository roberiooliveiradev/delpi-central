# shared/delpi_auth/authorization.py
from functools import wraps
import inspect

from .context_resolver import resolve_user_context
from .authz_core import has_permission, has_any_permission, has_all_permissions


def require_auth():
    def decorator(fn):
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def async_wrapper(*args, **kwargs):
                user = resolve_user_context()

                if not user:
                    raise Exception("Unauthorized")

                return await fn(*args, **kwargs)

            return async_wrapper

        @wraps(fn)
        def sync_wrapper(*args, **kwargs):
            user = resolve_user_context()

            if not user:
                raise Exception("Unauthorized")

            return fn(*args, **kwargs)

        return sync_wrapper

    return decorator


def require_permission(permission_code: str):
    def decorator(fn):
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def async_wrapper(*args, **kwargs):
                user = resolve_user_context()

                if not user:
                    raise Exception("Unauthorized")

                if getattr(user, "is_superadmin", False):
                    return await fn(*args, **kwargs)

                if not has_permission(user, permission_code):
                    raise Exception("Forbidden")

                return await fn(*args, **kwargs)

            return async_wrapper

        @wraps(fn)
        def sync_wrapper(*args, **kwargs):
            user = resolve_user_context()

            if not user:
                raise Exception("Unauthorized")

            if getattr(user, "is_superadmin", False):
                return fn(*args, **kwargs)

            if not has_permission(user, permission_code):
                raise Exception("Forbidden")

            return fn(*args, **kwargs)

        return sync_wrapper

    return decorator


def require_any_permission(permission_codes):
    def decorator(fn):
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def async_wrapper(*args, **kwargs):
                user = resolve_user_context()

                if not user:
                    raise Exception("Unauthorized")

                if getattr(user, "is_superadmin", False):
                    return await fn(*args, **kwargs)

                if not has_any_permission(user, permission_codes):
                    raise Exception("Forbidden")

                return await fn(*args, **kwargs)

            return async_wrapper

        @wraps(fn)
        def sync_wrapper(*args, **kwargs):
            user = resolve_user_context()

            if not user:
                raise Exception("Unauthorized")

            if getattr(user, "is_superadmin", False):
                return fn(*args, **kwargs)

            if not has_any_permission(user, permission_codes):
                raise Exception("Forbidden")

            return fn(*args, **kwargs)

        return sync_wrapper

    return decorator


def require_all_permissions(permission_codes):
    def decorator(fn):
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def async_wrapper(*args, **kwargs):
                user = resolve_user_context()

                if not user:
                    raise Exception("Unauthorized")

                if getattr(user, "is_superadmin", False):
                    return await fn(*args, **kwargs)

                if not has_all_permissions(user, permission_codes):
                    raise Exception("Forbidden")

                return await fn(*args, **kwargs)

            return async_wrapper

        @wraps(fn)
        def sync_wrapper(*args, **kwargs):
            user = resolve_user_context()

            if not user:
                raise Exception("Unauthorized")

            if getattr(user, "is_superadmin", False):
                return fn(*args, **kwargs)

            if not has_all_permissions(user, permission_codes):
                raise Exception("Forbidden")

            return fn(*args, **kwargs)

        return sync_wrapper

    return decorator


def require_superadmin():
    def decorator(fn):
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def async_wrapper(*args, **kwargs):
                user = resolve_user_context()

                if not user:
                    raise Exception("Unauthorized")

                if not getattr(user, "is_superadmin", False):
                    raise Exception("Forbidden")

                return await fn(*args, **kwargs)

            return async_wrapper

        @wraps(fn)
        def sync_wrapper(*args, **kwargs):
            user = resolve_user_context()

            if not user:
                raise Exception("Unauthorized")

            if not getattr(user, "is_superadmin", False):
                raise Exception("Forbidden")

            return fn(*args, **kwargs)

        return sync_wrapper

    return decorator