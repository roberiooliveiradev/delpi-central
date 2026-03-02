# app/middleware/auth_middleware.py

from fastapi import Request
from fastapi.responses import JSONResponse
from delpi_auth.jwt_validator import validate_token


async def jwt_middleware(request: Request, call_next):

    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    token = auth_header.replace("Bearer ", "").strip()

    try:
        payload = validate_token(token)

        request.state.user = payload

    except Exception:
        return JSONResponse(status_code=401, content={"detail": "Invalid token"})

    return await call_next(request)