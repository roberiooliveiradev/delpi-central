"""Provider-neutral semantic capabilities for external integrations (MCP + legacy GPT)."""

from app.application.external_capabilities.constants import (
    EXTERNAL_INTERNAL_ERROR_MESSAGE,
    MCP_TOOL_SEARCH_PRODUCTS,
    PRODUCT_SEARCH_DEFAULT_PAGE_SIZE,
    PRODUCT_SEARCH_MAX_PAGE_SIZE,
    PRODUCT_SEARCH_RESPONSE_FIELDS,
)

__all__ = [
    "EXTERNAL_INTERNAL_ERROR_MESSAGE",
    "MCP_TOOL_SEARCH_PRODUCTS",
    "PRODUCT_SEARCH_DEFAULT_PAGE_SIZE",
    "PRODUCT_SEARCH_MAX_PAGE_SIZE",
    "PRODUCT_SEARCH_RESPONSE_FIELDS",
    "search_products",
]


def __getattr__(name: str):
    if name == "search_products":
        from app.application.external_capabilities.product_search_service import (
            search_products,
        )

        return search_products
    raise AttributeError(name)
