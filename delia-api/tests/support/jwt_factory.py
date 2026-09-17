"""Deterministic local RS256 JWT helpers for delia-api auth tests."""

from __future__ import annotations

import time
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt
from jose.backends import RSAKey


ISSUER = "https://keycloak.test/auth/realms/delpi"
AUDIENCE = "delpi-central"
KID = "delia-test-key"


def generate_rsa_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def public_jwk(public_pem: bytes) -> dict[str, Any]:
    key = RSAKey(public_pem, algorithm="RS256")
    data = key.to_dict()
    data["kid"] = KID
    data["use"] = "sig"
    data["alg"] = "RS256"
    return data


def mint_token(
    private_pem: bytes,
    *,
    claims: dict[str, Any] | None = None,
    audience: str = AUDIENCE,
    issuer: str = ISSUER,
    expires_in: int = 3600,
) -> str:
    now = int(time.time())
    payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "user@example.com",
        "name": "Test User",
        "iat": now,
        "exp": now + expires_in,
        "iss": issuer,
        "aud": audience,
    }
    if claims:
        payload.update(claims)
    return jwt.encode(payload, private_pem, algorithm="RS256", headers={"kid": KID})
