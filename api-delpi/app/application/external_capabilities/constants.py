"""Provider-neutral constants for approved external Product Master capabilities."""

from __future__ import annotations

PRODUCT_SEARCH_MAX_PAGE_SIZE = 50
PRODUCT_SEARCH_DEFAULT_PAGE_SIZE = 50

# Organizational allowlist (004A.2 / PLUGIN-001). External field → internal key.
PRODUCT_SEARCH_FIELD_MAP: dict[str, str] = {
    "product_code": "code",
    "description": "description",
    "group_category": "group_code",
}
PRODUCT_SEARCH_RESPONSE_FIELDS: tuple[str, ...] = tuple(PRODUCT_SEARCH_FIELD_MAP.keys())

# customer_reference and every other Product DTO field remain DENY_BY_DEFAULT.
PRODUCT_SEARCH_DENIED_QUERY_PARAMS: frozenset[str] = frozenset({"customer_reference"})

EXTERNAL_INTERNAL_ERROR_MESSAGE = "Internal error while processing the request."

MCP_TOOL_SEARCH_PRODUCTS = "search_products"
MCP_TOOL_SEARCH_PRODUCTS_TITLE = "Search DELPI products"
MCP_GATEWAY_PATH = "/mcp"
MCP_GATEWAY_ROOT = "/apps/api-delpi"
