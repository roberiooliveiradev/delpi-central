from app.security.jwt_validator import validate_token

from fastapi import Request
from fastapi.responses import JSONResponse
import jwt
from app.config import settings

PUBLIC_PATHS = {
    "/", 
    "/docs", 
    "/redoc", 
    "/openapi.json",
    "/system/login"
}

def is_public_path(path: str) -> bool:
    # Remove prefixo do root_path se existir
    prefix = "/apps/api-delpi"
    if path.startswith(prefix):
        path = path[len(prefix):]

    if path in PUBLIC_PATHS:
        return True

    if path.startswith("/products/") and path.endswith("/structure/excel"):
        return True

    return False

async def jwt_middleware(request: Request, call_next):
    path = request.url.path

    if is_public_path(path):
        return await call_next(request)

    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"errors":[{"code":"unauthorized","message":"Token não informado","path":"_global"}]}
        )

    token = auth_header.replace("Bearer ", "").strip()

    try:
        payload = validate_token(token)
        request.state.user = payload
    except ValueError:
        return JSONResponse(
            status_code=401,
            content={"errors":[{"code":"invalid_token","message":"Token inválido","path":"_global"}]}
        )

    return await call_next(request)