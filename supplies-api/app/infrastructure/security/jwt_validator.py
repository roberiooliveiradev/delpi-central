from __future__ import annotations

import jwt
from jwt import PyJWKClient

from app.domain.entities import AuthenticatedIdentity
from app.domain.exceptions import AuthenticationError
from app.infrastructure.config.settings import Settings


class KeycloakJwtValidator:
    def __init__(self) -> None:
        self.jwks_url = Settings.KEYCLOAK_JWKS_URL
        self.issuer = Settings.KEYCLOAK_ISSUER
        self.audience = Settings.KEYCLOAK_AUDIENCE
        self.algorithms = [
            algorithm.strip()
            for algorithm in Settings.JWT_ALGORITHMS.split(",")
            if algorithm.strip()
        ]
        self._jwk_client = PyJWKClient(self.jwks_url) if self.jwks_url else None

    def validate(self, token: str) -> AuthenticatedIdentity:
        if not self._jwk_client or not self.issuer:
            raise AuthenticationError("JWT validation is not configured")

        try:
            signing_key = self._jwk_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=self.algorithms or ["RS256"],
                audience=self.audience if self.audience else None,
                issuer=self.issuer,
                options={
                    "require": ["sub", "exp", "iss"],
                    "verify_aud": bool(self.audience),
                },
            )
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Invalid token") from exc

        sub = claims.get("sub")
        email = claims.get("email")
        if not sub or not email:
            raise AuthenticationError("Invalid token claims")

        return AuthenticatedIdentity(
            sub=str(sub),
            email=str(email),
            name=str(claims["name"]) if claims.get("name") else None,
        )
