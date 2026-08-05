from __future__ import annotations

import inspect
from functools import wraps
from typing import Callable, Iterable

from fastapi import Request

from commercial_app.application.security.commercial_permissions import has_any_permission
from commercial_app.core.responses import fail


def _extract_request(args: tuple, kwargs: dict) -> Request | None:
    for value in kwargs.values():
        if isinstance(value, Request):
            return value
    for value in args:
        if isinstance(value, Request):
            return value
    return None


def require_any_permission(*permission_codes: str) -> Callable:
    """Exige ao menos uma permissão (ou role equivalente) do JWT/RBAC."""

    def decorator(fn: Callable) -> Callable:
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def async_wrapper(*args, **kwargs):
                request = _extract_request(args, kwargs)
                user = getattr(request.state, "user", None) if request else None
                if user is None:
                    return fail("Não autenticado.", 401)
                if not has_any_permission(user, permission_codes):
                    return fail("Sem permissão para esta operação.", 403)
                return await fn(*args, **kwargs)

            return async_wrapper

        @wraps(fn)
        def sync_wrapper(*args, **kwargs):
            request = _extract_request(args, kwargs)
            user = getattr(request.state, "user", None) if request else None
            if user is None:
                return fail("Não autenticado.", 401)
            if not has_any_permission(user, permission_codes):
                return fail("Sem permissão para esta operação.", 403)
            return fn(*args, **kwargs)

        return sync_wrapper

    return decorator
