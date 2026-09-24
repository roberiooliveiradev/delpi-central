"""MCP transport schemas for DAVI / api-delpi tools (interface adapter boundary)."""

from __future__ import annotations

from typing import Any

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


class DiscoverDelpiInformationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(..., min_length=1, description="Natural-language information need")
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="Bounded candidate count (optional)",
    )


class DiscoverCandidateSemanticHints(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity: str | None = None
    shape: str | None = None
    tags: list[str] = Field(default_factory=list)


class DiscoverCandidatePaginationHints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supports_page: bool
    supports_page_size: bool


class DiscoverDelpiInformationCandidate(BaseModel):
    """One opaque, actor-bound discovery candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_token: str
    description: str
    semantic_hints: DiscoverCandidateSemanticHints
    required_arguments: list[str]
    argument_schema: dict[str, Any]
    pagination_hints: DiscoverCandidatePaginationHints
    retrieval_score: float
    action_id: str


class CapabilitySurfaceOutput(BaseModel):
    """Stable MCP envelope for live ``agent_directives`` projection.

    Nested ``agent_directives`` remains a controlled dynamic mapping owned by
    ``davi_agent_intelligence.json`` / ``DaviAgentIntelligenceService`` — do not
    duplicate every mutable field as Pydantic properties here.
    """

    model_config = ConfigDict(extra="forbid")

    agent_directives: dict[str, Any]


class DiscoverDelpiInformationOutput(BaseModel):
    """Runtime envelope for discover_delpi_information structuredContent."""

    model_config = ConfigDict(extra="forbid")

    query: str
    top_k: int
    candidate_count: int
    eligible_action_count: int
    candidates: list[DiscoverDelpiInformationCandidate]
    capability_surface: CapabilitySurfaceOutput


class ExecuteDelpiInformationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_token: str = Field(..., min_length=1, description="Opaque token from discovery")
    arguments: dict[str, Any] | None = Field(
        default=None,
        description="Schema-bounded arguments for the discovered candidate",
    )


class ExecuteDelpiInformationOutput(BaseModel):
    """Runtime envelope for execute_delpi_information structuredContent.

    ``data`` is capability-dependent (approved projection / bounded payload).
    """

    model_config = ConfigDict(extra="forbid")

    action_id: str
    status: str
    entity: str | None = None
    shape: str | None = None
    projection: str
    data: Any = None
    truncated: bool
    is_complete: bool
    response_bytes: int | None = None
    error: str | None = None


def discover_delpi_information_input_json_schema() -> dict:
    schema = DiscoverDelpiInformationInput.model_json_schema()
    schema["title"] = "discover_delpi_informationArguments"
    schema["additionalProperties"] = False
    return schema


def discover_delpi_information_output_json_schema() -> dict:
    schema = DiscoverDelpiInformationOutput.model_json_schema()
    schema["title"] = "discover_delpi_informationOutput"
    schema["additionalProperties"] = False
    return schema


def execute_delpi_information_input_json_schema() -> dict:
    schema = ExecuteDelpiInformationInput.model_json_schema()
    schema["title"] = "execute_delpi_informationArguments"
    schema["additionalProperties"] = False
    return schema


def execute_delpi_information_output_json_schema() -> dict:
    schema = ExecuteDelpiInformationOutput.model_json_schema()
    schema["title"] = "execute_delpi_informationOutput"
    schema["additionalProperties"] = False
    return schema
