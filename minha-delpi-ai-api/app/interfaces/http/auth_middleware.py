from flask import g, request

from app.domain.exceptions.auth_exceptions import AuthenticationError
from app.infrastructure.security.jwt_validator import KeycloakJwtValidator


def register_auth_middleware(app):
    validator = KeycloakJwtValidator()

    @app.before_request
    def authenticate_request():
        g.current_user = None
        g.access_token = None
        g.internal_service = False

        from delpi_auth.service_token import headers_have_valid_internal_service_token

        if headers_have_valid_internal_service_token(dict(request.headers)):
            g.internal_service = True
            g.current_user = type(
                "InternalServiceUser",
                (),
                {
                    "sub": "internal-service",
                    "email": "service@delpi.internal",
                    "name": "Serviço Interno",
                },
            )()
            return None

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
