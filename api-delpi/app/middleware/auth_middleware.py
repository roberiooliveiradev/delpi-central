from fastapi import Request
from fastapi.responses import JSONResponse
from app.security.jwt_validator import validate_token

PUBLIC_PATHS = {
    "/",
    "/docs",
    "/openapi.json",
    "/system/login",
}

PREFIX = "/apps/api-delpi"

def normalize_path(path: str) -> str:
    # remove prefixo se existir
    if path.startswith(PREFIX):
        path = path[len(PREFIX):] or "/"

    # remove barra final (exceto raiz)
    if path != "/":
        path = path.rstrip("/")

    return path

def is_public_path(path: str) -> bool:
    return normalize_path(path) in PUBLIC_PATHS

async def jwt_middleware(request: Request, call_next):
    path = normalize_path(request.url.path)

    # DEBUG temporário (pode remover depois)
    print("PATH:", path)

    if is_public_path(path):
        return await call_next(request)

    auth_header = (
        request.headers.get("Authorization")
        or request.headers.get("X-Forwarded-Authorization")
    )

    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={
                "errors": [
                    {
                        "code": "unauthorized",
                        "message": "Token não informado",
                        "path": "_global",
                    }
                ]
            },
        )

    token = auth_header.replace("Bearer ", "").strip()

    try:
        payload = validate_token(token)
        request.state.user = payload
    except ValueError:
        return JSONResponse(
            status_code=401,
            content={
                "errors": [
                    {
                        "code": "invalid_token",
                        "message": "Token inválido",
                        "path": "_global",
                    }
                ]
            },
        )

    return await call_next(request)