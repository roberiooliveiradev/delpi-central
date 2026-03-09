# shared/delpi_auth/middleware/flask_auth.py

from flask import request, g
from types import SimpleNamespace

from ..jwt_validator import validate_token


def authenticate():

    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1]

    claims = validate_token(token)

    g.user = SimpleNamespace(
        id=claims.get("sub"),
        email=claims.get("email"),
        name=claims.get("name"),
        permissions=claims.get("permissions", []),
        roles=claims.get("roles", []),
        groups=claims.get("groups", []),
        is_superadmin=claims.get("is_superadmin", False),
    )

    return None