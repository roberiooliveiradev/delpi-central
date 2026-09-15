"""MCP mount routing — no unsafe slash redirect; ChatGPT Origin allowlist."""

from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import (
    TransportSecurityMiddleware,
    TransportSecuritySettings,
)
from starlette.routing import Mount

from app.interface.mcp.asgi import normalize_mcp_mount_path
from app.interface.mcp.resource_metadata import public_host_allowed_for_mcp


def test_normalize_mcp_mount_path_exact_only() -> None:
    assert normalize_mcp_mount_path("/mcp") == "/mcp/"
    assert normalize_mcp_mount_path("/apps/api-delpi/mcp") == "/apps/api-delpi/mcp/"
    assert normalize_mcp_mount_path("/mcp/") == "/mcp/"
    assert normalize_mcp_mount_path("/mcp/extra") == "/mcp/extra"
    assert normalize_mcp_mount_path("/health") == "/health"


def test_chatgpt_origins_are_allowlisted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://minhadelpi.com.br")
    _hosts, origins = public_host_allowed_for_mcp()
    assert "https://chatgpt.com" in origins
    assert "https://chat.openai.com" in origins
    assert "https://minhadelpi.com.br" in origins


@pytest.mark.asyncio
async def test_chatgpt_origin_accepted_by_transport_security(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://minhadelpi.com.br")
    hosts, origins = public_host_allowed_for_mcp()
    mw = TransportSecurityMiddleware(
        TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=hosts,
            allowed_origins=origins,
        )
    )

    class _Req:
        def __init__(self, origin: str | None) -> None:
            headers = {
                "host": "minhadelpi.com.br",
                "content-type": "application/json",
            }
            if origin is not None:
                headers["origin"] = origin
            self.headers = headers

    assert await mw.validate_request(_Req(None), is_post=True) is None
    assert await mw.validate_request(_Req("https://chatgpt.com"), is_post=True) is None
    assert await mw.validate_request(_Req("https://chat.openai.com"), is_post=True) is None
    evil = await mw.validate_request(_Req("https://evil.example"), is_post=True)
    assert evil is not None
    assert evil.status_code == 403


@pytest.mark.asyncio
async def test_post_mcp_without_trailing_slash_does_not_redirect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: ChatGPT uses canonical URL without slash; Mount must not 307."""
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://minhadelpi.com.br")
    hosts, origins = public_host_allowed_for_mcp()
    mcp = FastMCP(
        name="routing-probe",
        streamable_http_path="/",
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=hosts,
            allowed_origins=origins,
        ),
    )
    child = mcp.streamable_http_app()
    app = FastAPI()

    @app.middleware("http")
    async def _rewrite(request, call_next):
        path = request.scope.get("path") or ""
        normalized = normalize_mcp_mount_path(path)
        if normalized != path:
            request.scope["path"] = normalized
            if "raw_path" in request.scope:
                request.scope["raw_path"] = normalized.encode("ascii")
        return await call_next(request)

    app.mount("/mcp", child)

    body = (
        b'{"jsonrpc":"2.0","id":1,"method":"initialize","params":'
        b'{"protocolVersion":"2024-11-05","capabilities":{},'
        b'"clientInfo":{"name":"d","version":"0"}}}'
    )

    async def _status(path: str, *, origin: str | None = None) -> dict:
        status: dict = {}

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            if message["type"] == "http.response.start":
                status["code"] = message["status"]
                status["headers"] = {
                    k.decode(): v.decode() for k, v in message.get("headers", [])
                }

        headers = [
            (b"host", b"minhadelpi.com.br"),
            (b"content-type", b"application/json"),
            (b"accept", b"application/json, text/event-stream"),
        ]
        if origin:
            headers.append((b"origin", origin.encode()))
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "https",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": headers,
            "client": ("1.1.1.1", 123),
            "server": ("minhadelpi.com.br", 443),
            "root_path": "",
        }
        await app(scope, receive, send)
        return status

    async with child.router.lifespan_context(child):
        bare = await _status("/mcp")
        assert bare["code"] == 200
        assert "location" not in {k.lower() for k in bare.get("headers", {})}

        slash = await _status("/mcp/")
        assert slash["code"] == 200

        chatgpt = await _status("/mcp", origin="https://chatgpt.com")
        assert chatgpt["code"] == 200
