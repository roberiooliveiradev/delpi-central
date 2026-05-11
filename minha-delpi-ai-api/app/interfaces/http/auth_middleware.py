from flask import g, request

from app.domain.exceptions.auth_exceptions import AuthenticationError
from app.infrastructure.security.jwt_validator import KeycloakJwtValidator


def register_auth_middleware(app):
    validator = KeycloakJwtValidator()

    @app.before_request
    def authenticate_request():
        g.current_user = None
        g.access_token = None

        auth_header = request.headers.get("Authorization", "")

        if not auth_header:
            return None

        if not auth_header.startswith("Bearer "):
            raise AuthenticationError("Authentication required")

        token = auth_header.removeprefix("Bearer ").strip()

        if not token:
            raise AuthenticationError("Authentication required")

        g.current_user = validator.validate(token)
        g.access_token = token

        return None
