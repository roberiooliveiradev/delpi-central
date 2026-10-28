import asyncio
import base64
import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt as jose_jwt

import delpi_auth.jwt_validator as jwt_validator_module
import delpi_auth.middleware.fastapi_auth as fastapi_auth_module
from delpi_auth.authorization import require_any_permission
from delpi_auth.context_resolver import resolve_user_context

from engineering_app.main import app
from engineering_app.middleware.auth_middleware import jwt_middleware
from engineering_app.middleware.request_observability_middleware import (
    get_request_id,
    request_observability_middleware,
)

TEST_ISSUER = "https://keycloak.test/realms/delpi"
TEST_AUDIENCE = "delpi-central"
TEST_KID = "test-key-1"
ENGINEERING_ACCESS = "engineering.access"


@pytest.fixture
def client():
    return TestClient(app)


# --- JWT harness: assinatura RSA real, JWKS e issuer/audience controlados ---


def _b64url_uint(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _generate_rsa_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _private_pem(private_key) -> bytes:
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def _jwks_for(public_key, kid: str = TEST_KID) -> dict:
    numbers = public_key.public_numbers()
    return {
        "keys": [
            {
                "kty": "RSA",
                "kid": kid,
                "use": "sig",
                "alg": "RS256",
                "n": _b64url_uint(numbers.n),
                "e": _b64url_uint(numbers.e),
            }
        ]
    }


def _sign(private_key, kid: str = TEST_KID, **claims) -> str:
    now = int(time.time())
    payload = {
        "sub": "user-1",
        "email": "user@delpi.test",
        "name": "Test User",
        "iss": TEST_ISSUER,
        "aud": TEST_AUDIENCE,
        "iat": now,
        "exp": now + 300,
    }
    payload.update(claims)
    return jose_jwt.encode(
        payload,
        _private_pem(private_key),
        algorithm="RS256",
        headers={"kid": kid},
    )


@pytest.fixture
def jwks_env(monkeypatch):
    """Validação real de assinatura com JWKS/issuer/audience de teste.

    Somente o fetch de JWKS e as envs de issuer/audience são controlados —
    o decode do token percorre o caminho real do python-jose.
    """
    private_key = _generate_rsa_key()
    other_key = _generate_rsa_key()
    jwks = _jwks_for(private_key.public_key())

    monkeypatch.setenv("KEYCLOAK_ISSUER", TEST_ISSUER)
    monkeypatch.setenv("KEYCLOAK_AUDIENCE", TEST_AUDIENCE)
    monkeypatch.setenv("JWT_ALGORITHMS", "RS256")
    monkeypatch.setattr(jwt_validator_module, "_jwks_cache", None)
    monkeypatch.setattr(jwt_validator_module, "_get_jwks", lambda: jwks)

    def _make(**claims):
        return _sign(private_key, **claims)

    def _make_wrong_key(**claims):
        return _sign(other_key, **claims)

    return {"make_token": _make, "make_wrong_key_token": _make_wrong_key}


# --- Core /me harness: resolução RBAC controlada, sem rede ---


def rbac_payload(permissions, **overrides) -> dict:
    data = {
        "id": "user-1",
        "email": "user@delpi.test",
        "name": "Test User",
        "roles": [],
        "groups": [],
        "permissions": list(permissions),
        "is_superadmin": False,
    }
    data.update(overrides)
    return data


@pytest.fixture
def core_rbac(monkeypatch):
    """Substitui a resolução Core /me por resultado/exceção controlados.

    ``state["behavior"]`` é ("data", payload) ou ("raise", excecao).
    """
    state = {"behavior": ("data", rbac_payload([ENGINEERING_ACCESS]))}

    async def _fake_load_user_rbac(token, *, force_refresh=False):
        kind, value = state["behavior"]
        if kind == "raise":
            raise value
        if kind == "fn":
            return value(token)
        return value

    monkeypatch.setattr(
        fastapi_auth_module, "load_user_rbac", _fake_load_user_rbac
    )
    return state


@pytest.fixture(autouse=True)
def _reset_rbac_state():
    fastapi_auth_module._RBAC_CACHE.clear()
    fastapi_auth_module._RBAC_LOCKS.clear()
    yield
    fastapi_auth_module._RBAC_CACHE.clear()
    fastapi_auth_module._RBAC_LOCKS.clear()


# --- Harness de autorização: rota protegida existente apenas em teste ---


@pytest.fixture
def probe_client():
    probe_app = FastAPI()
    # Mesma ordem do app produtivo: observability envolve o JWT.
    probe_app.middleware("http")(jwt_middleware)
    probe_app.middleware("http")(request_observability_middleware)

    @probe_app.get("/probe", operation_id="test_engineering_access_probe")
    @require_any_permission([ENGINEERING_ACCESS])
    def _probe():
        return {"status": "granted"}

    @probe_app.get("/probe/whoami", operation_id="test_engineering_whoami")
    @require_any_permission([ENGINEERING_ACCESS])
    def _whoami():
        user = resolve_user_context()
        return {
            "email": user.email,
            "permissions": list(user.permissions),
            "principal_type": user.principal_type,
        }

    @probe_app.get("/probe/items/{item_id}", operation_id="test_engineering_item")
    @require_any_permission([ENGINEERING_ACCESS])
    def _item(item_id: str):
        return {"item_id": item_id}

    @probe_app.get("/probe/context", operation_id="test_engineering_context")
    @require_any_permission([ENGINEERING_ACCESS])
    async def _context():
        # Interleaving real: suspende o coroutine para sobrepor requests.
        await asyncio.sleep(0.01)
        user = resolve_user_context()
        return {
            "request_id": get_request_id(),
            "email": user.email,
            "principal_type": user.principal_type,
        }

    @probe_app.get("/probe/boom", operation_id="test_engineering_boom")
    @require_any_permission([ENGINEERING_ACCESS])
    def _boom():
        raise RuntimeError("sensitive-boom-internal")

    # Rota pública (allowlist) que falha — prova a instrumentação de 500
    # fora do boundary de auth do delpi_auth.
    @probe_app.get("/health", operation_id="test_public_boom")
    def _public_boom():
        raise RuntimeError("public-boom-internal")

    return TestClient(probe_app)


@pytest.fixture
def probe_asgi_app():
    """Probe app como ASGI puro — testes de concorrência via AsyncClient."""
    from delpi_auth.authorization import require_any_permission
    from delpi_auth.context_resolver import resolve_user_context

    probe_app = FastAPI()
    probe_app.middleware("http")(jwt_middleware)
    probe_app.middleware("http")(request_observability_middleware)

    @probe_app.get("/probe/context", operation_id="test_engineering_context")
    @require_any_permission([ENGINEERING_ACCESS])
    async def _context():
        await asyncio.sleep(0.01)
        user = resolve_user_context()
        return {
            "request_id": get_request_id(),
            "email": user.email,
            "principal_type": user.principal_type,
        }

    return probe_app
