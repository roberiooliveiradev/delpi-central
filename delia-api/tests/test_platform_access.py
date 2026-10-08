from __future__ import annotations

import gzip
import json
import time
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from delpi_auth import jwt_validator

from app.application.platform_access import PlatformAccessContext
from app.composition.root_composer import _bounded_http_get
from app.create_app import create_app
from app.infrastructure.auth.core_platform_access import CorePlatformAccessAdapter
from tests.test_http_absolute_deadline import (
    _await_abort,
    _body_trickle,
    _header_trickle,
    _read_request,
    _serve,
    _status_line_trickle,
)
from tests.support.jwt_factory import (
    AUDIENCE,
    ISSUER,
    generate_rsa_keypair,
    mint_token,
    public_jwk,
)
from tests.support.test_access_probe import (
    TEST_PLATFORM_ACCESS_PATH,
    register_test_platform_access_probe,
)


@pytest.fixture()
def rsa_keys():
    return generate_rsa_keypair()


@pytest.fixture(autouse=True)
def jwt_env(monkeypatch, rsa_keys):
    _private_pem, public_pem = rsa_keys
    monkeypatch.setenv("KEYCLOAK_ISSUER", ISSUER)
    monkeypatch.setenv("KEYCLOAK_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("JWT_ALGORITHMS", "RS256")
    jwks = {"keys": [public_jwk(public_pem)]}
    monkeypatch.setattr(jwt_validator, "_get_jwks", lambda: jwks)
    jwt_validator._jwks_cache = None
    yield
    jwt_validator._jwks_cache = None


@pytest.fixture()
def private_pem(rsa_keys):
    return rsa_keys[0]


def _core_response(status: int, payload: dict | None):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = payload
    return response


def test_valid_token_and_core_me_builds_access_context(private_pem):
    token = mint_token(
        private_pem,
        claims={"permissions": ["fake.jwt.permission"], "roles": ["jwt-role"]},
    )
    http_get = MagicMock(
        return_value=_core_response(
            200,
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "name": "Core Name",
                "email": "user@example.com",
                "roles": ["core-role"],
                "groups": ["core-group"],
                "permissions": ["real.core.permission"],
                "is_superadmin": False,
            },
        )
    )
    adapter = CorePlatformAccessAdapter(
        core_api_url="http://core-api:8000",
        timeout_seconds=2.0,
        http_get=http_get,
    )

    context = adapter.resolve(token)

    assert context.effective_permissions == ("real.core.permission",)
    assert "fake.jwt.permission" not in context.effective_permissions
    assert context.roles == ("core-role",)
    assert context.groups == ("core-group",)
    assert context.source == "CORE"
    http_get.assert_called_once()
    args, kwargs = http_get.call_args
    assert args[0] == "http://core-api:8000/me"
    assert kwargs["headers"]["Authorization"] == f"Bearer {token}"


def test_jwt_fake_permissions_never_become_effective_authority(private_pem):
    token = mint_token(
        private_pem,
        claims={
            "permissions": ["fake.jwt.permission"],
            "roles": ["jwt-admin"],
            "groups": ["jwt-group"],
            "is_superadmin": True,
        },
    )
    http_get = MagicMock(
        return_value=_core_response(
            200,
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "name": "Core Name",
                "email": "user@example.com",
                "roles": ["operator"],
                "groups": ["ops"],
                "permissions": ["real.core.permission"],
                "is_superadmin": False,
            },
        )
    )
    adapter = CorePlatformAccessAdapter(
        core_api_url="http://core-api:8000",
        timeout_seconds=2.0,
        http_get=http_get,
    )
    context = adapter.resolve(token)
    assert context.effective_permissions == ("real.core.permission",)
    assert context.roles == ("operator",)
    assert context.groups == ("ops",)
    assert context.is_superadmin is False


@pytest.mark.parametrize(
    "factory",
    [
        lambda pem: "",  # missing handled by middleware; adapter empty
        lambda pem: "not-a-jwt",
        lambda pem: mint_token(pem, expires_in=-10),
        lambda pem: mint_token(pem, issuer="https://evil.example/realms/x"),
        lambda pem: mint_token(pem, audience="wrong-audience"),
    ],
)
def test_invalid_tokens_fail_closed(private_pem, factory):
    from app.application.ports.platform_access_port import AuthenticationError

    token = factory(private_pem)
    adapter = CorePlatformAccessAdapter(
        core_api_url="http://core-api:8000",
        timeout_seconds=2.0,
        http_get=MagicMock(),
    )
    with pytest.raises(AuthenticationError):
        adapter.resolve(token)


def test_missing_jwt_config_fails_closed(monkeypatch, private_pem):
    from app.application.ports.platform_access_port import AuthenticationError

    monkeypatch.delenv("KEYCLOAK_AUDIENCE", raising=False)
    token = mint_token(private_pem)
    adapter = CorePlatformAccessAdapter(
        core_api_url="http://core-api:8000",
        timeout_seconds=2.0,
        http_get=MagicMock(),
    )
    with pytest.raises(AuthenticationError):
        adapter.resolve(token)


def test_unknown_signing_key_fails_closed(private_pem, monkeypatch):
    from app.application.ports.platform_access_port import AuthenticationError

    monkeypatch.setattr(jwt_validator, "_get_jwks", lambda: {"keys": []})
    token = mint_token(private_pem)
    adapter = CorePlatformAccessAdapter(
        core_api_url="http://core-api:8000",
        timeout_seconds=2.0,
        http_get=MagicMock(),
    )
    with pytest.raises(AuthenticationError):
        adapter.resolve(token)


def test_core_unavailable_fails_closed(private_pem):
    from app.application.ports.platform_access_port import AuthorityUnavailableError

    token = mint_token(private_pem)
    http_get = MagicMock(side_effect=ConnectionError("down"))
    adapter = CorePlatformAccessAdapter(
        core_api_url="http://core-api:8000",
        timeout_seconds=2.0,
        http_get=http_get,
    )
    with pytest.raises(AuthorityUnavailableError):
        adapter.resolve(token)


def test_core_401_is_authentication_failure(private_pem):
    from app.application.ports.platform_access_port import AuthenticationError

    token = mint_token(private_pem)
    http_get = MagicMock(return_value=_core_response(401, {"detail": "nope"}))
    adapter = CorePlatformAccessAdapter(
        core_api_url="http://core-api:8000",
        timeout_seconds=2.0,
        http_get=http_get,
    )
    with pytest.raises(AuthenticationError):
        adapter.resolve(token)


def test_core_malformed_payload_fails_closed(private_pem):
    from app.application.ports.platform_access_port import AuthorityUnavailableError

    token = mint_token(private_pem)
    http_get = MagicMock(return_value=_core_response(200, {"email": "only-email"}))
    adapter = CorePlatformAccessAdapter(
        core_api_url="http://core-api:8000",
        timeout_seconds=2.0,
        http_get=http_get,
    )
    with pytest.raises(AuthorityUnavailableError):
        adapter.resolve(token)


def _app_with_test_probe(*, platform_access_provider):
    app = create_app(testing=True, platform_access_provider=platform_access_provider)
    register_test_platform_access_probe(app)
    return app


def test_middleware_establishes_core_backed_context_not_jwt(private_pem):
    class FakeProvider:
        def resolve(self, bearer_token: str) -> PlatformAccessContext:
            assert bearer_token
            return PlatformAccessContext(
                user_id="11111111-1111-1111-1111-111111111111",
                name="Core Name",
                email="user@example.com",
                roles=("core-role",),
                groups=("core-group",),
                effective_permissions=("real.core.permission",),
                is_superadmin=False,
            )

    app = _app_with_test_probe(platform_access_provider=FakeProvider())
    token = mint_token(
        private_pem,
        claims={"permissions": ["fake.jwt.permission"]},
    )
    response = app.test_client().get(
        TEST_PLATFORM_ACCESS_PATH,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["effective_permissions"] == ["real.core.permission"]
    assert "fake.jwt.permission" not in body["effective_permissions"]
    assert body["roles"] == ["core-role"]
    assert body["groups"] == ["core-group"]
    assert body["is_superadmin"] is False
    assert body["source"] == "CORE"
    assert "email" not in body
    assert "name" not in body
    assert "access_token" not in body


def test_production_app_has_no_access_context_route():
    app = create_app(testing=True, platform_access_provider=None)
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/health" in rules
    assert "/access-context" not in rules
    assert TEST_PLATFORM_ACCESS_PATH not in rules


def test_missing_authorization_rejected():
    app = _app_with_test_probe(
        platform_access_provider=SimpleNamespace(resolve=lambda *_: None),
    )
    response = app.test_client().get(TEST_PLATFORM_ACCESS_PATH)
    assert response.status_code == 401
    assert response.get_json()["code"] == "unauthenticated"


def test_malformed_bearer_rejected():
    app = _app_with_test_probe(
        platform_access_provider=SimpleNamespace(resolve=lambda *_: None),
    )
    response = app.test_client().get(
        TEST_PLATFORM_ACCESS_PATH,
        headers={"Authorization": "Token abc"},
    )
    assert response.status_code == 401


def test_empty_bearer_rejected():
    app = _app_with_test_probe(
        platform_access_provider=SimpleNamespace(resolve=lambda *_: None),
    )
    response = app.test_client().get(
        TEST_PLATFORM_ACCESS_PATH,
        headers={"Authorization": "Bearer "},
    )
    assert response.status_code == 401
    assert response.get_json()["code"] == "unauthenticated"


def test_health_remains_public_without_token():
    app = create_app(testing=True, platform_access_provider=None)
    response = app.test_client().get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "available"


def test_health_independent_of_core_provider():
    class Boom:
        def resolve(self, bearer_token: str):
            raise RuntimeError("should not be called")

    app = create_app(testing=True, platform_access_provider=Boom())
    response = app.test_client().get("/health")
    assert response.status_code == 200


def test_provider_absent_fail_closed_on_protected_route():
    app = _app_with_test_probe(platform_access_provider=None)
    response = app.test_client().get(
        TEST_PLATFORM_ACCESS_PATH,
        headers={"Authorization": "Bearer not-validated-here"},
    )
    assert response.status_code == 503
    assert response.get_json()["code"] == "authority_unavailable"


# LOOP-03R2B-CLOSEOUT-01 — Core /me total wall-clock deadline.
# The production binding (_bounded_http_get, the same callable the
# composer wires) puts the whole GET under ONE absolute deadline:
# DNS, connect, TLS, status line, headers and body. A per-recv
# scalar would let a trickling Core /me hold the auth path open
# far past core_timeout_seconds. Real socket servers below prove
# termination at the configured bound — fail closed, never a JWT
# fallback.

_CORE_BOUND = 0.4
_CORE_ELAPSED_MAX = 1.0

_CORE_ME_PAYLOAD = {
    "id": "11111111-1111-1111-1111-111111111111",
    "name": "Core Name",
    "email": "user@example.com",
    "roles": ["core-role"],
    "groups": ["core-group"],
    "permissions": ["real.core.permission"],
    "is_superadmin": False,
}


def _real_core_adapter(server):
    return CorePlatformAccessAdapter(
        core_api_url=f"http://127.0.0.1:{server.getsockname()[1]}",
        timeout_seconds=_CORE_BOUND,
        http_get=_bounded_http_get,
    )


def _assert_core_deadline(token, writer):
    from app.application.ports.platform_access_port import (
        AuthorityUnavailableError,
    )

    server, stop, observed = _serve(writer)
    try:
        started = time.monotonic()
        with pytest.raises(AuthorityUnavailableError):
            _real_core_adapter(server).resolve(token)
        elapsed = time.monotonic() - started
        assert elapsed < _CORE_ELAPSED_MAX, f"elapsed {elapsed:.2f}s"
        _await_abort(observed)
        assert observed  # server observed the connection die
    finally:
        stop.set()
        server.close()


def test_core_me_status_line_trickle_absolute_deadline(private_pem):
    """A Core /me trickling the status line must abort at the bound —
    before this fix the scalar timeout renewed per recv."""
    _assert_core_deadline(
        mint_token(private_pem), _status_line_trickle
    )


def test_core_me_header_trickle_absolute_deadline(private_pem):
    """Header bytes trickled below the inactivity slice must abort
    at the absolute deadline before end-of-headers."""
    _assert_core_deadline(
        mint_token(private_pem), _header_trickle
    )


def test_core_me_body_trickle_absolute_deadline(private_pem):
    """An endless 1-byte-per-50ms /me body must not outlive the
    configured bound."""
    _assert_core_deadline(mint_token(private_pem), _body_trickle)


def _core_me_gzip_lowercase(conn, observed):
    """Core /me JSON served gzipped with lowercase header names."""
    try:
        if not _read_request(conn):
            return
        body = gzip.compress(json.dumps(_CORE_ME_PAYLOAD).encode())
        conn.sendall(
            b"HTTP/1.1 200 OK\r\n"
            b"content-type: application/json\r\n"
            b"content-encoding: gzip\r\n"
            b"content-length: " + str(len(body)).encode() + b"\r\n\r\n" + body
        )
    except OSError as exc:
        observed.append(type(exc).__name__)
    finally:
        conn.close()


def _core_me_fast_json(conn, observed):
    try:
        if not _read_request(conn):
            return
        body = json.dumps(_CORE_ME_PAYLOAD).encode()
        conn.sendall(
            b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
            b"Content-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body
        )
    except OSError as exc:
        observed.append(type(exc).__name__)
    finally:
        conn.close()


def test_core_me_gzip_lowercase_headers_parsed(private_pem):
    """Gzipped /me JSON with lowercase headers still parses into the
    platform access context — decoding happens inside the bounded
    drain, never as an unbounded second step."""
    token = mint_token(private_pem)
    server, stop, _ = _serve(_core_me_gzip_lowercase)
    try:
        context = _real_core_adapter(server).resolve(token)
        assert context.effective_permissions == ("real.core.permission",)
        assert context.roles == ("core-role",)
        assert context.source == "CORE"
    finally:
        stop.set()
        server.close()


def test_core_me_fast_path_real_transport(private_pem):
    """A fast complete /me response resolves normally through the
    bounded production transport."""
    token = mint_token(private_pem)
    server, stop, _ = _serve(_core_me_fast_json)
    try:
        context = _real_core_adapter(server).resolve(token)
        assert context.effective_permissions == ("real.core.permission",)
        assert context.groups == ("core-group",)
        assert context.is_superadmin is False
    finally:
        stop.set()
        server.close()
