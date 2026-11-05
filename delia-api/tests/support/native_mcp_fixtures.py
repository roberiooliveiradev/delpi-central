"""Native MCPToolset test support — in-process owner servers.

The production wiring builds ``MCPToolset(<endpoint url>)`` per
specialist. Tests substitute ONLY the client transport: a real
``mcp.server.mcpserver.MCPServer`` in-process exposes the owner tool
surface (names + input schemas), while ``process_tool_call`` and the
governed invoke path stay 100% real — the in-process server never
executes a business call, exactly like production.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Mapping

from fastmcp import Client
from mcp.server.mcpserver import MCPServer
from pydantic_ai.mcp import MCPToolset

import app.infrastructure.orchestration.pydantic_ai_investigation as _inv_mod


def owner_tool_server(
    name: str,
    tools: Mapping[str, str],
) -> MCPServer:
    """Build an in-process MCP server exposing ``tools``.

    ``tools`` maps remote tool name → description. Input schemas are
    derived from the generated handler signature (``arguments`` dict),
    matching the DELPI envelope shape; business calls are never
    executed because ``process_tool_call`` intercepts before the wire.
    """
    server = MCPServer(name)
    for remote_name, description in tools.items():
        def _make():
            def handler(
                query: str = "",
                candidate_token: str = "",
                arguments: dict | None = None,
            ):
                return {
                    "error": "test server must never execute business calls"
                }

            return handler

        server.add_tool(
            _make(), name=remote_name, description=description
        )
    return server


def recording_owner_tool_server(
    name: str,
    tools: Mapping[str, tuple[str, Any]],
    calls: list,
) -> MCPServer:
    """Variant recording any business call that reaches the server —
    used to prove ``process_tool_call`` intercepts before the wire."""
    server = MCPServer(name)
    for remote_name, (description, result) in tools.items():
        def _make(tool_name=remote_name, tool_result=result):
            def handler(
                query: str = "",
                candidate_token: str = "",
                arguments: dict | None = None,
            ):
                calls.append(tool_name)
                return tool_result

            return handler

        server.add_tool(
            _make(), name=remote_name, description=description
        )
    return server


def alpha_beta_servers() -> dict:
    """Default two-group owner surface matching ``_providers()`` —
    ``alpha.search_items`` and ``beta.read_guidance``."""
    return {
        "alpha": owner_tool_server(
            "alpha", {"search_items": "read items"}
        ),
        "beta": owner_tool_server(
            "beta", {"read_guidance": "read guidance"}
        ),
    }


@contextmanager
def native_toolset_stub(servers: Mapping[str, MCPServer]):
    """Patch the toolset builder with in-process MCP servers.

    ``servers`` keys are group ids (``alpha``, ``davi``...). The fake
    provider resolves ``endpoint="mcp-test://<group_id>"`` through the
    same public contract chain as production; only the SDK client
    transport is substituted.
    """
    original = _inv_mod._build_native_mcp_toolset

    def _factory(config, *, process_tool_call):
        group_id = str(config.endpoint).split("://", 1)[1]
        server = servers[group_id]
        return MCPToolset(
            Client(server), process_tool_call=process_tool_call
        )

    _inv_mod._build_native_mcp_toolset = _factory
    try:
        yield
    finally:
        _inv_mod._build_native_mcp_toolset = original
