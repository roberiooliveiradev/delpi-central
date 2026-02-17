# app/infrastructure/security/jwt_service.py

from authlib.jose import jwt
from authlib.jose.errors import JoseError
from urllib.request import urlopen
import json
import os


class JWTService:

    def __init__(self):
        self.jwks_url = os.getenv("KEYCLOAK_JWKS_URL")
        self.issuer = os.getenv("KEYCLOAK_ISSUER")
        self.audience = os.getenv("KEYCLOAK_AUDIENCE")

    def _get_jwks(self):
        response = urlopen(self.jwks_url)
        return json.loads(response.read())

    def verify_token(self, token: str):
        try:
            jwks = self._get_jwks()

            # Decodifica e verifica assinatura
            claims = jwt.decode(token, jwks)

            # Valida expiração automaticamente
            claims.validate()

            # 🔐 Validação manual de issuer
            if claims.get("iss") != self.issuer:
                raise Exception("Invalid issuer")

            # # 🔐 Validação manual de audience
            # token_aud = claims.get("aud")

            # if isinstance(token_aud, list):
            #     if self.audience not in token_aud:
            #         raise Exception("Invalid audience")
            # else:
            #     if token_aud != self.audience:
            #         raise Exception("Invalid audience")
            if claims.get("azp") != self.audience:
                raise Exception("Invalid client")


            return claims

        except JoseError as e:
            raise Exception(f"Token inválido: {str(e)}")
