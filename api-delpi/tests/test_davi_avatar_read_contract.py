"""DAVI official avatar — read(capability="avatar") delivery contract.

DAVI-PROFILE-V1 / AVATAR-INLINE-MCP-V1: the static ficha asset is delivered
as a canonical ``ImageContent`` block (shared ``delpi_mcp.avatar_image``)
while ``structuredContent`` keeps the published ``readOutput`` envelope —
the avatar metadata rides the free-form ``data`` field so the advertised
outputSchema stays honest for every capability.
"""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path

import pytest
from mcp.types import ImageContent

from app.interface.mcp.schemas import ReadOutput
from app.interface.mcp.server import create_mcp_server

DAVI_AVATAR_SHA256 = (
    "94494e3a0c5ccc4672f4cb765e7e23785d48001f2a66514a86f4d356f281b98e"
)
DAVI_AVATAR_ASSET = (
    Path(__file__).resolve().parents[1]
    / "app/assets/characters/davi/avatar-v1.png"
)


@pytest.mark.asyncio
async def test_read_avatar_returns_image_content_block() -> None:
    result = await create_mcp_server().call_tool(
        "read", {"capability": "avatar", "arguments": {}}
    )
    assert result.is_error is False
    kinds = [type(c).__name__ for c in result.content]
    assert "ImageContent" in kinds
    image = next(c for c in result.content if isinstance(c, ImageContent))
    assert image.mime_type == "image/png"
    raw = base64.b64decode(image.data)
    assert hashlib.sha256(raw).hexdigest() == DAVI_AVATAR_SHA256
    assert raw == DAVI_AVATAR_ASSET.read_bytes()


@pytest.mark.asyncio
async def test_read_avatar_structured_content_matches_output_schema() -> None:
    """structuredContent must validate against the published readOutput."""
    result = await create_mcp_server().call_tool(
        "read", {"capability": "avatar", "arguments": {}}
    )
    assert result.is_error is False
    envelope = ReadOutput.model_validate(result.structured_content)
    assert envelope.capability == "avatar"
    assert envelope.status == "ok"
    assert envelope.is_complete is True
    assert envelope.truncated is False
    data = envelope.data
    assert data["character_id"] == "davi"
    assert data["avatar_status"] == "OFFICIAL_AVATAR_APPROVED"
    assert data["mime_type"] == "image/png"
    assert data["sha256"] == DAVI_AVATAR_SHA256
    assert data["content_delivery"] == "image_block"
    assert data["bytes"] == envelope.response_bytes


@pytest.mark.asyncio
async def test_read_avatar_delivers_only_davi_asset() -> None:
    """Sibling specialists' assets can never be served through DAVI."""
    result = await create_mcp_server().call_tool(
        "read", {"capability": "avatar", "arguments": {}}
    )
    image = next(c for c in result.content if isinstance(c, ImageContent))
    assert base64.b64decode(image.data) == DAVI_AVATAR_ASSET.read_bytes()
    assert result.structured_content["data"]["avatar_reference"].endswith(
        "app/assets/characters/davi/avatar-v1.png"
    )


@pytest.mark.asyncio
async def test_read_avatar_capability_is_case_insensitive_but_scoped() -> None:
    result = await create_mcp_server().call_tool(
        "read", {"capability": " AVATAR ", "arguments": {}}
    )
    assert result.is_error is False
    assert result.structured_content["capability"] == "AVATAR"
    assert any(isinstance(c, ImageContent) for c in result.content)


@pytest.mark.asyncio
async def test_read_avatar_does_not_shadow_catalog_capabilities() -> None:
    """The avatar intercept stays a single literal — catalog reads fail
    closed for unknown ids and never route through the asset path."""
    result = await create_mcp_server().call_tool(
        "read", {"capability": "avatar_x", "arguments": {}}
    )
    assert result.is_error is True
    assert result.structured_content["code"] == "CAPABILITY_NOT_ALLOWED"


@pytest.mark.asyncio
async def test_read_tool_surface_unchanged() -> None:
    """No new tool was added for the avatar — read stays one of four."""
    tools = await create_mcp_server().list_tools()
    assert sorted(t.name for t in tools) == [
        "analyze",
        "get_context",
        "knowledge",
        "read",
    ]
