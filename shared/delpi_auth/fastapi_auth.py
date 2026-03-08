from functools import wraps
from fastapi import Request, HTTPException

from .authz_core import has_permission


def require_permission(permission_code: str):

    def decorator(func):

        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):

            user = getattr(request.state, "user", None)

            if not user:
                raise HTTPException(status_code=401, detail="Unauthorized")

            if not has_permission(user, permission_code):
                raise HTTPException(status_code=403, detail="Forbidden")

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator