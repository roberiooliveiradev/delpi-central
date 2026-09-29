"""Shared MCP transport AuthN (S3) — unit tests with synthetic injectables.

No real JWTs, no Keycloak, no production credentials. The validator, service
token gate and base middleware are all injected doubles.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Mapping

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from delpi_mcp.auth import (
    McpTransportAuthPolicy,
    is_mcp_data_path,
    mcp_transport_auth,
)

RESOURCE = "https://minhadelpi.com.br/apps/example-api/mcp"
SCOPES = ("openid", "profile", "email", "mcp:tools")

VALID_CLAIMS: dict[str, Any] = {
    "sub": "u-1",
    "aud": ["delpi-central", RESOURCE],
    "scope": "openid profile email mcp:tools",
}


def _request(path: str, headers: dict[str, str] | None = None) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [
            (k.lower().encode("latin-1"), v.encode("latin-1"))
            for k, v in (headers or {}).items()
        ],
        "client": ("127.0.0.1", 1234),
        "server": ("test", 80),
        "state": {},
    }
    return Request(scope)


def _run(request: Request, **kwargs) -> Response:
    return asyncio.run(mcp_transport_auth(request, _next_ok, **kwargs))


def _recording_challenge(calls: list):
    def _challenge(*, error=None, error_description=None) -> str:
        calls.append((error, error_description))
        return f'Bearer realm="test" error="{error}"'

    return _challenge


def _policy(calls=None, *, redecorate: bool = True, resource: str = RESOURCE) -> McpTransportAuthPolicy:
    return McpTransportAuthPolicy(
        resolve_resource_audience=lambda: resource,
        required_scopes=SCOPES,
        challenge=_recording_challenge(calls if calls is not None else []),
        redecorate_base_401=redecorate,
    )


async def _ok_base(request: Request, call_next):
    request.state.user = "established-by-base"
    return await call_next(request)


async def _next_ok(request: Request) -> Response:
    return JSONResponse({"ok": True})


def _deny_all(_request: Request) -> bool:
    return True


def _allow(_request: Request) -> bool:
    return False


def _validator(claims: Mapping[str, Any]):
    def _v(_token: str) -> Mapping[str, Any]:
        return claims

    return _v


def _defaults(**overrides):
    kwargs = {
        "policy": _policy(),
        "token_validator": _validator(VALID_CLAIMS),
        "service_token_gate": _allow,
        "base_auth_middleware": _ok_base,
    }
    kwargs.update(overrides)
    return kwargs


def test_is_mcp_data_path():
    assert is_mcp_data_path("/mcp")
    assert is_mcp_data_path("/mcp/")
    assert is_mcp_data_path("/mcp/tools/call")
    assert not is_mcp_data_path("/mcpfoo")
    assert not is_mcp_data_path("/.well-known/oauth-protected-resource")
    assert not is_mcp_data_path("/api/data")


def test_service_token_forbidden() -> None:
    calls: list = []
    resp = _run(
        _request("/mcp", {"Authorization": "Bearer x"}),
        **_defaults(policy=_policy(calls), service_token_gate=_deny_all),
    )
    assert resp.status_code == 401
    assert calls == [("invalid_token", "User authentication required")]


def test_missing_bearer_fails_closed() -> None:
    calls: list = []
    resp = _run(_request("/mcp"), **_defaults(policy=_policy(calls)))
    assert resp.status_code == 401
    assert "WWW-Authenticate" in resp.headers
    assert calls == [("invalid_token", "Authentication required")]


def test_wrong_scheme_fails_closed() -> None:
    resp = _run(_request("/mcp", {"Authorization": "Basic abc"}), **_defaults())
    assert resp.status_code == 401


def test_empty_bearer_fails_closed() -> None:
    resp = _run(_request("/mcp", {"Authorization": "Bearer   "}), **_defaults())
    assert resp.status_code == 401


def test_validator_exception_fails_closed() -> None:
    calls: list = []

    def _boom(_t: str):
        raise ValueError("bad signature")

    resp = _run(
        _request("/mcp", {"Authorization": "Bearer x"}),
        **_defaults(policy=_policy(calls), token_validator=_boom),
    )
    assert resp.status_code == 401
    assert calls == [("invalid_token", "Access token validation failed")]


def test_wrong_audience_fails_closed() -> None:
    claims = {**VALID_CLAIMS, "aud": ["delpi-central"]}
    calls: list = []
    resp = _run(
        _request("/mcp", {"Authorization": "Bearer x"}),
        **_defaults(policy=_policy(calls), token_validator=_validator(claims)),
    )
    assert resp.status_code == 401
    assert calls == [("invalid_token", "MCP resource audience is required")]


def test_missing_audience_claim_fails_closed() -> None:
    claims = {k: v for k, v in VALID_CLAIMS.items() if k != "aud"}
    resp = _run(
        _request("/mcp", {"Authorization": "Bearer x"}),
        **_defaults(token_validator=_validator(claims)),
    )
    assert resp.status_code == 401


def test_missing_scope_fails_closed() -> None:
    claims = {**VALID_CLAIMS, "scope": "openid profile email"}
    calls: list = []
    resp = _run(
        _request("/mcp", {"Authorization": "Bearer x"}),
        **_defaults(policy=_policy(calls), token_validator=_validator(claims)),
    )
    assert resp.status_code == 401
    assert calls == [("insufficient_scope", "Required OAuth scopes are missing")]


def test_empty_resource_config_fails_closed() -> None:
    """Unresolvable resource URL must never skip audience validation."""
    calls: list = []
    resp = _run(
        _request("/mcp", {"Authorization": "Bearer x"}),
        **_defaults(policy=_policy(calls, resource="")),
    )
    assert resp.status_code == 401
    assert calls == [("invalid_token", "MCP resource audience is required")]


def test_valid_token_delegates_once() -> None:
    seen: list[str] = []

    async def _base(request: Request, call_next):
        seen.append("base")
        request.state.user = "u-1"
        return await call_next(request)

    resp = _run(
        _request("/mcp", {"Authorization": "Bearer x"}),
        **_defaults(base_auth_middleware=_base),
    )
    assert resp.status_code == 200
    assert seen == ["base"]


def test_base_not_called_on_pre_auth_failure() -> None:
    seen: list[str] = []

    async def _base(request: Request, call_next):
        seen.append("base")
        return await call_next(request)

    _run(_request("/mcp"), **_defaults(base_auth_middleware=_base))
    assert seen == []


def test_base_401_redecorated_when_enabled() -> None:
    calls: list = []

    async def _base(request: Request, call_next):
        return JSONResponse(
            {"detail": "Unauthorized"},
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
        )

    resp = _run(
        _request("/mcp", {"Authorization": "Bearer x"}),
        **_defaults(policy=_policy(calls), base_auth_middleware=_base),
    )
    assert resp.status_code == 401
    assert resp.headers["WWW-Authenticate"] == 'Bearer realm="test" error="invalid_token"'
    assert calls == [("invalid_token", "Authentication required")]


def test_base_401_preserved_when_redecorate_disabled() -> None:
    calls: list = []

    async def _base(request: Request, call_next):
        return JSONResponse(
            {"detail": "Unauthorized"},
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
        )

    resp = _run(
        _request("/mcp", {"Authorization": "Bearer x"}),
        **_defaults(policy=_policy(calls, redecorate=False), base_auth_middleware=_base),
    )
    assert resp.status_code == 401
    assert resp.headers["WWW-Authenticate"] == "Bearer"
    assert calls == []


def test_domain_403_not_rewritten() -> None:
    async def _base(request: Request, call_next):
        return JSONResponse({"detail": "Forbidden"}, status_code=403)

    resp = _run(
        _request("/mcp", {"Authorization": "Bearer x"}),
        **_defaults(base_auth_middleware=_base),
    )
    assert resp.status_code == 403
    assert "WWW-Authenticate" not in resp.headers


def test_no_partial_identity_on_failure() -> None:
    request = _request("/mcp")
    _run(request, **_defaults())
    assert not hasattr(request.state, "user")


def test_token_never_logged(caplog) -> None:
    secret = "s3cr3t-token-value"
    with caplog.at_level(logging.WARNING, logger="delpi_mcp.auth"):
        _run(
            _request("/mcp", {"Authorization": f"Bearer {secret}"}),
            **_defaults(
                token_validator=lambda _t: (_ for _ in ()).throw(ValueError("x"))
            ),
        )
    assert secret not in caplog.text
    assert "claims" not in caplog.text.lower()
