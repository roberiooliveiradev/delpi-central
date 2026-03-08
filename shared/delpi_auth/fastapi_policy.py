from functools import wraps
from fastapi import Request, HTTPException

from .policy_engine import evaluate_policy


def policy(name: str):

    def decorator(func):

        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):

            user = getattr(request.state, "user", None)

            if not user:
                raise HTTPException(status_code=401, detail="Unauthorized")

            if user.get("is_superadmin"):
                return await func(request, *args, **kwargs)

            allowed = evaluate_policy(name, user, **kwargs)

            if not allowed:
                raise HTTPException(status_code=403, detail="Forbidden")

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator