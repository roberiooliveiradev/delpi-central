"""Backward-compat do contrato ``public_path_checker`` de jwt_middleware.

Garante que consumidores podem restringir a política pública por chamada
sem mutar ``request.scope["path"]`` e sem alterar o default canônico dos
demais consumidores.
"""

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse

from delpi_auth.middleware.fastapi_auth import is_public_path, jwt_middleware


def _request(path: str, headers: dict | None = None) -> Request:
    raw_headers = [
        (name.lower().encode(), value.encode())
        for name, value in (headers or {}).items()
    ]
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "query_string": b"",
            "headers": raw_headers,
        }
    )


async def _next(_request):
    return JSONResponse(status_code=200, content={"ok": True})


@pytest.mark.asyncio
async def test_default_policy_unchanged_when_checker_omitted():
    """Sem checker: o default da lib continua aceitando /foo/docs."""
    response = await jwt_middleware(_request("/foo/docs"), _next)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_custom_checker_restricts_broad_default_paths():
    """Checker estrito força autenticação onde o default aceitaria."""
    strict = lambda path: path == "/health"  # noqa: E731

    public_response = await jwt_middleware(
        _request("/health"), _next, public_path_checker=strict
    )
    assert public_response.status_code == 200

    protected = await jwt_middleware(
        _request("/foo/docs"), _next, public_path_checker=strict
    )
    assert protected.status_code == 401  # auth exigida, sem mutation de scope


@pytest.mark.asyncio
async def test_custom_checker_does_not_mutate_scope_path():
    request = _request("/v1/secret")
    await jwt_middleware(request, _next, public_path_checker=lambda p: False)
    assert request.scope["path"] == "/v1/secret"


def test_is_public_path_default_contract_preserved():
    """O default global da lib não muda: política ampla continua canônica."""
    assert is_public_path("/apps/api-delpi/health") is True
    assert is_public_path("/foo/openapi.json") is True
