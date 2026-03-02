from fastapi import Request, HTTPException


def require_permission(permission_code: str):
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):

            user = getattr(request.state, "user", None)

            if not user:
                raise HTTPException(status_code=401, detail="Unauthorized")

            if user.get("is_superadmin"):
                return await func(request, *args, **kwargs)

            permissions = user.get("permissions", [])

            if permission_code not in permissions:
                raise HTTPException(status_code=403, detail="Forbidden")

            return await func(request, *args, **kwargs)

        return wrapper
    return decorator