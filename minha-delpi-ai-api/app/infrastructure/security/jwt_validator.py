from __future__ import annotations

import uuid

import jwt
from jwt import PyJWKClient

from app.domain.entities.authenticated_user import AuthenticatedUser
from app.domain.exceptions.auth_exceptions import InvalidClaimsError, InvalidTokenError
from app.infrastructure.config.settings import Settings


class KeycloakJwtValidator:
    def __init__(self):
        self.jwks_url = Settings.KEYCLOAK_JWKS_URL
        self.issuer = Settings.KEYCLOAK_ISSUER
        self.audience = Settings.KEYCLOAK_AUDIENCE
        self.algorithms = [
            algorithm.strip()
            for algorithm in Settings.JWT_ALGORITHMS.split(",")
            if algorithm.strip()
        ]

        self._jwk_client = PyJWKClient(self.jwks_url) if self.jwks_url else None

    def validate(self, token: str) -> AuthenticatedUser:
        if not self._jwk_client or not self.issuer or not self.audience:
            raise InvalidTokenError("JWT validation is not configured")

        try:
            signing_key = self._jwk_client.get_signing_key_from_jwt(token)

            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=self.algorithms,
                audience=self.audience,
                issuer=self.issuer,
                options={
                    "require": ["sub", "exp", "iss"],
                },
            )
        except jwt.PyJWTError as exc:
            raise InvalidTokenError("Invalid token") from exc

        return self._claims_to_user(claims)

    def _claims_to_user(self, claims: dict) -> AuthenticatedUser:
        sub = claims.get("sub")
        email = claims.get("email")
        name = claims.get("name")

        if not sub or not email:
            raise InvalidClaimsError("Token missing required claims")

        try:
            uuid.UUID(str(sub))
        except ValueError as exc:
            raise InvalidClaimsError("Invalid user identifier") from exc

        return AuthenticatedUser(
            sub=str(sub),
            email=str(email),
            name=str(name) if name else None,
            roles=self._extract_roles(claims),
            groups=self._extract_groups(claims),
        )

    def _extract_roles(self, claims: dict) -> list[str]:
        roles: set[str] = set()

        realm_access = claims.get("realm_access") or {}
        for role in realm_access.get("roles") or []:
            roles.add(str(role))

        resource_access = claims.get("resource_access") or {}
        for client_data in resource_access.values():
            for role in (client_data or {}).get("roles") or []:
                roles.add(str(role))

        return sorted(roles)

    def _extract_groups(self, claims: dict) -> list[str]:
        groups = claims.get("groups") or []
        return sorted(str(group) for group in groups)
