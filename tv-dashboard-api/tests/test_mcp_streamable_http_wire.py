"""MCP transport wire — get_playlist_context ImageContent projection (S2).

Exercises the REAL Streamable-HTTP transport stack:

    create_mcp_server -> mcp_http_app -> JSON-RPC initialize -> tools/call

over an in-process ASGI client. Only domain prerequisites are mocked
(dispatch payload + artifact bytes + auth ContextVars) — the bridge, the
mcp 2.x CallToolResult model and the JSON-RPC serializer run for real.

Regression intent: prove that a ready ``editor_live`` canonical_stage
artifact produces a spec-compliant ``{"type": "image", "data", "mimeType"}``
content block on the wire, additive to TextContent + structuredContent.
Whether a downstream host (e.g. ChatGPT connector) forwards that block to
the model is a host concern — the protocol contract asserted here is ours.
"""

from __future__ import annotations

import asyncio
import base64
import json
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import pytest

from delpi_auth.request_context import (
    reset_current_user,
    reset_request_authorization,
    set_current_user,
    set_request_authorization,
)

from tv_app.interface.mcp import tool_bridge
from tv_app.interface.mcp.asgi import mcp_http_app
from tv_app.interface.mcp.server import create_mcp_server

_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def _rendered(status: str, source: str | None = "editor_live") -> dict:
    return {
        "status": status,
        "kind": "canonical_stage",
        "source": source,
        "revision": 7,
        "width": 1920,
        "height": 1080,
        "mimeType": "image/png",
    }


def _context_payload(rendered: dict) -> dict:
    return {
        "playlistId": "pl-1",
        "revision": 7,
        "slidePreview": {
            "slideId": "sl-1",
            "previewUrl": "https://example.invalid/signed",
            "rendered": rendered,
        },
    }


def _viewer() -> SimpleNamespace:
    return SimpleNamespace(
        id="u-1",
        email="u@delpi.local",
        is_superadmin=False,
        permissions=["tv-dashboard.read"],
        roles=[],
        groups=[],
    )


async def _tools_call_context(payload: dict) -> dict:
    """Run initialize + tools/call against the real streamable-HTTP app."""
    mcp = create_mcp_server()
    app = mcp_http_app(mcp)
    async with mcp.session_manager.run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://localhost:8877"
        ) as client:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }
            init = await client.post(
                "/",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "wire-test", "version": "0"},
                    },
                },
            )
            assert init.status_code == 200
            await client.post(
                "/",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                },
            )
            tok_u = set_current_user(_viewer())
            tok_a = set_request_authorization("Bearer test")
            try:
                with (
                    patch.object(
                        tool_bridge._dispatch,
                        "get_playlist_context",
                        return_value=payload,
                    ),
                    patch(
                        "tv_app.application.services.data"
                        ".slide_preview_render_service"
                        ".get_slide_preview_render_service"
                    ) as svc,
                ):
                    svc.return_value.read_rendered_png.return_value = _PNG
                    resp = await client.post(
                        "/",
                        headers=headers,
                        json={
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "tools/call",
                            "params": {
                                "name": "get_playlist_context",
                                "arguments": {
                                    "playlist_id": "pl-1",
                                    "slide_id": "sl-1",
                                    "include_preview": True,
                                },
                            },
                        },
                    )
            finally:
                reset_current_user(tok_u)
                reset_request_authorization(tok_a)
            assert resp.status_code == 200
            return resp.json()["result"]


def test_wire_contains_image_content_for_editor_live_artifact():
    """Raw wire: content=[text, image] + structuredContent for a ready
    editor_live canonical_stage artifact."""
    result = asyncio.run(
        _tools_call_context(_context_payload(_rendered("ready")))
    )
    content = result["content"]
    types = [c["type"] for c in content]
    assert "text" in types
    images = [c for c in content if c["type"] == "image"]
    assert len(images) == 1
    assert images[0]["mimeType"] == "image/png"
    raw = base64.b64decode(images[0]["data"])
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    assert result.get("structuredContent")


@pytest.mark.parametrize(
    "rendered",
    [
        _rendered("pending", source=None),
        _rendered("ready", source="editor_stage_capture"),
        _rendered("ready", source=None),
    ],
    ids=["pending", "offscreen_capture", "no_source"],
)
def test_wire_never_emits_image_without_editor_live(rendered):
    """No artifact / non-live provenance → text+structured only."""
    result = asyncio.run(_tools_call_context(_context_payload(rendered)))
    types = [c["type"] for c in result["content"]]
    assert "image" not in types
    assert "text" in types
    assert result.get("structuredContent")
    text = next(c["text"] for c in result["content"] if c["type"] == "text")
    assert json.loads(text)["data"]["slidePreview"]["rendered"]
