"""SURI avatar — AVATAR-INLINE-V1 hotfix regression.

Guards two proven defects:
1. ``read(entity="avatar")`` must be announced in the read tool schema —
   the Literal enum in ``app/interfaces/mcp/server.py`` is the source the
   MCP client validates against.
2. ``read(entity="avatar", action="get")`` must return the approved
   avatar bytes as an ``ImageContent`` block (MIME image/png).
"""

from __future__ import annotations


from mcp.types import ImageContent


def test_read_schema_announces_avatar_entity() -> None:
    """tools/list schema must accept entity='avatar' for read.

    The FastMCP decorator may wrap ``read`` into a FunctionTool, so the
    authoritative check targets the ``entity: Literal[...]`` block in the
    server source — that Literal is what generates the published JSON
    Schema enum.
    """
    import inspect
    import re

    from app.interfaces.mcp import server as mcp_server

    src = inspect.getsource(mcp_server)
    match = re.search(r"entity:\s*Literal\[([^\]]+)\]", src)
    assert match, "read entity Literal not found in server.py"
    assert '"avatar"' in match.group(1), (
        "avatar missing from read entity Literal — ChatGPT validates "
        "'avatar' is not one of [...]"
    )


def test_read_avatar_get_returns_image_content(
    access_context,
) -> None:
    """avatar.get delivers the official image as ImageContent block."""
    from app.interfaces.mcp import tool_bridge

    access_context()
    result = tool_bridge.tool_read(entity="avatar", action="get")
    assert result.is_error is False
    kinds = [type(c).__name__ for c in result.content]
    assert "ImageContent" in kinds
    image = next(
        c for c in result.content if isinstance(c, ImageContent)
    )
    assert image.mime_type == "image/png"
    assert image.data
