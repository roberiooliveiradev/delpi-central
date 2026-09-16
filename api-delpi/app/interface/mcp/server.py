"""FastMCP server exposing approved API DELPI semantic tools."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, TextContent, Tool as MCPTool, ToolAnnotations
from pydantic import ValidationError

from app.application.external_capabilities.constants import (
    EXTERNAL_INTERNAL_ERROR_MESSAGE,
    MCP_TOOL_SEARCH_PRODUCTS,
    MCP_TOOL_SEARCH_PRODUCTS_TITLE,
    PRODUCT_SEARCH_DEFAULT_PAGE_SIZE,
)
from app.application.external_capabilities.product_search_schemas import (
    SearchProductsInput,
    SearchProductsOutput,
    search_products_input_json_schema,
    search_products_output_json_schema,
)
from app.application.external_capabilities.product_search_service import search_products
from app.interface.mcp.branding import DAVI_MCP_INSTRUCTIONS
from app.interface.mcp.oauth_contract import (
    SEARCH_PRODUCTS_SECURITY_SCHEMES,
    mcp_www_authenticate_meta,
)
from app.interface.mcp.resource_metadata import public_host_allowed_for_mcp
from app.utils.logger import log_error

# Re-export for existing test imports that historically used server.SearchProductsInput.
__all__ = [
    "ApiDelpiFastMCP",
    "SearchProductsInput",
    "SearchProductsOutput",
    "VALIDATION_ERROR_CODE",
    "VALIDATION_ERROR_MESSAGE",
    "create_mcp_server",
    "validation_error_tool_result",
]

logger = logging.getLogger(__name__)

VALIDATION_ERROR_CODE = "VALIDATION_ERROR"
VALIDATION_ERROR_MESSAGE = "Invalid search parameters."


def validation_error_tool_result() -> CallToolResult:
    """Stable external validation failure — no Pydantic/framework details."""
    return CallToolResult(
        content=[TextContent(type="text", text=VALIDATION_ERROR_MESSAGE)],
        structuredContent={
            "code": VALIDATION_ERROR_CODE,
            "message": VALIDATION_ERROR_MESSAGE,
        },
        isError=True,
    )


class ApiDelpiFastMCP(FastMCP):
    """Promote OpenAI securitySchemes and project canonical input/output schemas."""

    async def list_tools(self) -> list[MCPTool]:
        tools = self._tool_manager.list_tools()
        listed: list[MCPTool] = []
        for info in tools:
            meta = dict(info.meta or {})
            schemes = meta.get("securitySchemes")
            input_schema = info.parameters
            output_schema = info.output_schema
            if info.name == MCP_TOOL_SEARCH_PRODUCTS:
                input_schema = search_products_input_json_schema()
                output_schema = search_products_output_json_schema()
            payload: dict[str, Any] = {
                "name": info.name,
                "title": info.title,
                "description": info.description or "",
                "inputSchema": input_schema,
                "outputSchema": output_schema,
                "annotations": info.annotations,
                "icons": info.icons,
                "_meta": meta or None,
            }
            if schemes:
                payload["securitySchemes"] = schemes
            listed.append(MCPTool.model_validate(payload))
        return listed

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Validate search_products against SearchProductsInput before FastMCP binding.

        FastMCP's generated arg model ignores unknown fields and would otherwise
        leak Pydantic messages when Field constraints are duplicated on the fn.
        """
        if name == MCP_TOOL_SEARCH_PRODUCTS:
            try:
                SearchProductsInput.model_validate(arguments or {})
            except ValidationError as exc:
                log_error(
                    f"mcp search_products validation rejected error_count={exc.error_count()}"
                )
                return validation_error_tool_result()
        return await super().call_tool(name, arguments)


def create_mcp_server() -> FastMCP:
    hosts, origins = public_host_allowed_for_mcp()
    mcp = ApiDelpiFastMCP(
        name="api-delpi",
        instructions=DAVI_MCP_INSTRUCTIONS,
        streamable_http_path="/",
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=hosts,
            allowed_origins=origins,
        ),
    )

    @mcp.tool(
        name=MCP_TOOL_SEARCH_PRODUCTS,
        title=MCP_TOOL_SEARCH_PRODUCTS_TITLE,
        description=(
            "Search DELPI Product Master through the canonical search use case "
            "and return only the approved external projection "
            "(product_code, description, group_category)."
        ),
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=False,
            title=MCP_TOOL_SEARCH_PRODUCTS_TITLE,
        ),
        meta={"securitySchemes": SEARCH_PRODUCTS_SECURITY_SCHEMES},
        structured_output=True,
    )
    def search_products_tool(
        code: str | None = None,
        description: str | None = None,
        group_code: str | None = None,
        page: int = 1,
        page_size: int = PRODUCT_SEARCH_DEFAULT_PAGE_SIZE,
    ) -> CallToolResult:
        # Constraints / unknown fields are owned by SearchProductsInput (call_tool + here).
        try:
            params = SearchProductsInput(
                code=code,
                description=description,
                group_code=group_code,
                page=page,
                page_size=page_size,
            )
        except ValidationError as exc:
            log_error(
                f"mcp search_products validation rejected error_count={exc.error_count()}"
            )
            return validation_error_tool_result()

        try:
            data = search_products(
                code=params.code,
                description=params.description,
                group_code=params.group_code,
                page=params.page,
                page_size=params.page_size,
                enforce_authz=True,
                tool_name=MCP_TOOL_SEARCH_PRODUCTS,
            )
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Product search completed.",
                    )
                ],
                structuredContent=data,
                isError=False,
            )
        except PermissionError as exc:
            message = str(exc) or "Forbidden"
            if message == "Unauthorized":
                return CallToolResult.model_validate(
                    {
                        "content": [
                            {
                                "type": "text",
                                "text": "Authentication required.",
                            }
                        ],
                        "isError": True,
                        "_meta": mcp_www_authenticate_meta(
                            error="invalid_token",
                            error_description="Authentication required",
                        ),
                    }
                )
            return CallToolResult(
                content=[TextContent(type="text", text="Forbidden")],
                isError=True,
            )
        except Exception as exc:
            log_error(f"mcp search_products failed: {exc}")
            raise RuntimeError(EXTERNAL_INTERNAL_ERROR_MESSAGE) from exc

    return mcp
