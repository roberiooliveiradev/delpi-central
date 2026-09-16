"""MCP transport schemas for DAVI / api-delpi tools (interface adapter boundary)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.application.external_capabilities.constants import (
    PRODUCT_SEARCH_DEFAULT_PAGE_SIZE,
    PRODUCT_SEARCH_MAX_PAGE_SIZE,
)


class SearchProductsInput(BaseModel):
    """Strict MCP input for Product Master search (closed schema)."""

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


class SearchProductsItemOutput(BaseModel):
    """Approved external item projection only."""

    model_config = ConfigDict(extra="forbid")

    product_code: str | None = None
    description: str | None = None
    group_category: str | None = None


class SearchProductsOutput(BaseModel):
    """Approved external page projection for tools/list outputSchema."""

    model_config = ConfigDict(extra="forbid")

    items: list[SearchProductsItemOutput]
    page: int
    page_size: int
    total: int
    total_pages: int


def search_products_input_json_schema() -> dict:
    """Canonical flat MCP inputSchema derived from SearchProductsInput."""
    schema = SearchProductsInput.model_json_schema()
    schema["title"] = "search_productsArguments"
    schema["additionalProperties"] = False
    return schema


def search_products_output_json_schema() -> dict:
    """Canonical MCP outputSchema matching runtime structuredContent."""
    schema = SearchProductsOutput.model_json_schema()
    schema["title"] = "search_productsOutput"
    schema["additionalProperties"] = False
    return schema
