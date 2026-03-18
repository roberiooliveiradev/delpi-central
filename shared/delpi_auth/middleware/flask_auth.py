# shared/delpi_auth/middleware/flask_auth.py

from flask import request, g
from types import SimpleNamespace

from ..jwt_validator import validate_token
from ..request_context import set_current_user, clear_current_user


def authenticate():
    clear_current_user()

    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        g.current_user = None
        g.user = None
        return None

    token = auth_header.split(" ", 1)[1]

    claims = validate_token(token)

    user = SimpleNamespace(
        id=claims.get("sub"),
        email=claims.get("email"),
        name=claims.get("name"),
        permissions=claims.get("permissions", []),
        roles=claims.get("roles", []),
        groups=claims.get("groups", []),
        is_superadmin=claims.get("is_superadmin", False),
    )

    # compatibilidade retroativa
    g.current_user = user
    g.user = user

    set_current_user(user)

    return None