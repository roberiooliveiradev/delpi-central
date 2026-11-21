"""Contract gates for OpenAI custom MCP discovery; no host or network access."""
import asyncio

from linux_ops_mcp.server import (
    APPROVED_TOOLS,
    CONTROL_TOOLS,
    OAUTH_SECURITY_SCHEMES,
    READ_TOOLS,
    create_mcp_server,
)


def test_only_approved_tools_and_explicit_oauth_security_schemes():
    async def discover():
        return await create_mcp_server().list_tools()

    tools = asyncio.run(discover())
    assert {tool.name for tool in tools} == APPROVED_TOOLS
    for tool in tools:
        body = tool.model_dump(by_alias=True)
        assert body["securitySchemes"] == OAUTH_SECURITY_SCHEMES
        if tool.name in READ_TOOLS:
            assert body["_meta"]["delpi/toolClass"] == "READ"
            assert body["annotations"]["readOnlyHint"] is True
            assert body["annotations"]["destructiveHint"] is False
        else:
            assert tool.name in CONTROL_TOOLS
            assert body["_meta"]["delpi/toolClass"] == "ACT"
            assert body["annotations"]["readOnlyHint"] is False
            assert body["annotations"]["destructiveHint"] is True
        assert not body["securitySchemes"][0]["type"] == "noauth"
