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
            claims = jwt.decode(token, jwks)

            claims.validate(
                iss=self.issuer,
                aud=self.audience
            )

            return claims

        except JoseError as e:
            raise Exception(f"Token inválido: {str(e)}")
