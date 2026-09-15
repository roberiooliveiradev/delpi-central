"""FastMCP server exposing approved API DELPI semantic tools."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field

from app.application.external_capabilities.constants import (
    EXTERNAL_INTERNAL_ERROR_MESSAGE,
    MCP_TOOL_SEARCH_PRODUCTS,
    MCP_TOOL_SEARCH_PRODUCTS_TITLE,
    PRODUCT_SEARCH_DEFAULT_PAGE_SIZE,
    PRODUCT_SEARCH_MAX_PAGE_SIZE,
)
from app.application.external_capabilities.product_search_service import search_products
from app.interface.mcp.resource_metadata import public_host_allowed_for_mcp
from app.utils.logger import log_error

logger = logging.getLogger(__name__)


class SearchProductsInput(BaseModel):
    """Strict input schema — unknown fields rejected; customer_reference forbidden."""

    model_config = ConfigDict(extra="forbid")

    code: str | None = Field(default=None, description="Product code filter")
    description: str | None = Field(default=None, description="Description filter")
    group_code: str | None = Field(default=None, description="Group/category filter")
    page: int = Field(default=1, ge=1, description="Page number (>= 1)")
    page_size: int = Field(
        default=PRODUCT_SEARCH_DEFAULT_PAGE_SIZE,
        ge=1,
        le=PRODUCT_SEARCH_MAX_PAGE_SIZE,
        description=f"Page size (1..{PRODUCT_SEARCH_MAX_PAGE_SIZE})",
    )


def create_mcp_server() -> FastMCP:
    hosts, origins = public_host_allowed_for_mcp()
    mcp = FastMCP(
        name="api-delpi",
        instructions=(
            "Read-only DELPI operational data tools. "
            "Use search_products for Product Master lookup only. "
            "Do not invent stock, pricing, customer, or supplier fields."
        ),
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
        structured_output=True,
    )
    def search_products_tool(
        code: str | None = None,
        description: str | None = None,
        group_code: str | None = None,
        page: int = 1,
        page_size: int = PRODUCT_SEARCH_DEFAULT_PAGE_SIZE,
    ) -> dict[str, Any]:
        # Validate with strict model (rejects customer_reference / unknown fields).
        try:
            params = SearchProductsInput(
                code=code,
                description=description,
                group_code=group_code,
                page=page,
                page_size=page_size,
            )
        except Exception as exc:
            raise ValueError(f"Invalid search_products arguments: {exc}") from exc

        try:
            return search_products(
                code=params.code,
                description=params.description,
                group_code=params.group_code,
                page=params.page,
                page_size=params.page_size,
                enforce_authz=True,
                tool_name=MCP_TOOL_SEARCH_PRODUCTS,
            )
        except PermissionError as exc:
            raise PermissionError(str(exc) or "Forbidden") from exc
        except Exception as exc:
            log_error(f"mcp search_products failed: {exc}")
            raise RuntimeError(EXTERNAL_INTERNAL_ERROR_MESSAGE) from exc

    return mcp
