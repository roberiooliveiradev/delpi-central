from __future__ import annotations

from flask import g, jsonify, request

from app.application.services.authorization_service import AuthorizationService
from app.domain.exceptions import AuthenticationError, CoreApiUnavailableError
from app.infrastructure.security.jwt_validator import KeycloakJwtValidator

PUBLIC_PATHS = frozenset({"/health", "/ready"})


def _normalize_path(path: str) -> str:
    if not path:
        return "/"
    normalized = path.split("?", 1)[0]
    if normalized != "/" and normalized.endswith("/"):
        normalized = normalized.rstrip("/")
    return normalized or "/"


def is_public_path(path: str) -> bool:
    return _normalize_path(path) in PUBLIC_PATHS


def register_auth_middleware(app) -> None:
    validator = KeycloakJwtValidator()
    authorization_service = AuthorizationService()

    @app.before_request
    def authenticate_and_authorize_frontier():
        g.identity = None
        g.access_token = None
        g.current_user = None

        path = _normalize_path(request.path)
        if is_public_path(path):
            return None

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"detail": "Unauthorized"}), 401

        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return jsonify({"detail": "Unauthorized"}), 401

        try:
            identity = validator.validate(token)
        except AuthenticationError:
            return jsonify({"detail": "Unauthorized"}), 401

        g.identity = identity
        g.access_token = token

        try:
            g.current_user = authorization_service.resolve_effective_user(
                token,
                keycloak_sub=identity.sub,
            )
        except CoreApiUnavailableError as exc:
            return jsonify({"detail": exc.message}), 503

        return None
