"""MCP transport schemas for DAVI / api-delpi tools (interface adapter boundary)."""

from __future__ import annotations

from typing import Any

from typing import Literal

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


class GetContextInput(BaseModel):
    """Closed input for the get_context semantic entry point."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["context", "catalog", "schema"] = Field(
        default="context",
        description=(
            "context: specialist identity, actor context, versions, limits "
            "and live directives; catalog: compact eligible capability "
            "list; schema: governed argument schema for one capability."
        ),
    )
    capability: str | None = Field(
        default=None,
        max_length=128,
        description="Technical action_id for action=schema (catalog metadata, not permission)",
    )


class GetContextOutput(BaseModel):
    """Runtime envelope for get_context structuredContent."""

    model_config = ConfigDict(extra="forbid")

    action: str
    status: str
    context: dict[str, Any] | None = None
    catalog: dict[str, Any] | None = None
    capability: dict[str, Any] | None = None


class KnowledgeInput(BaseModel):
    """Closed input for governed knowledge reads."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["search", "get", "sources"] = Field(
        ...,
        description=(
            "search: ranked excerpts for topic (+ optional subject/section "
            "narrowing); get: one section via topic+section; sources: "
            "corpus topic index."
        ),
    )
    topic: str | None = Field(
        default=None,
        max_length=64,
        description="Published corpus topic id (required for search/get)",
    )
    subject: str | None = Field(
        default=None,
        max_length=240,
        description="Optional subject/designation to rank sections deterministically",
    )
    section: str | None = Field(
        default=None,
        max_length=8,
        pattern=r"^s[0-9]{4}$",
        description="Stable section id returned in excerpts (required for get)",
    )
    corpus_version: int | None = Field(
        default=None,
        ge=1,
        le=1000,
        description="Published corpus version (default: latest)",
    )
    page: int = Field(default=1, ge=1, le=10000)
    page_size: int | None = Field(
        default=None,
        ge=1,
        le=3,
        description="Sections per page (1..3)",
    )


class KnowledgeOutput(BaseModel):
    """Runtime envelope for knowledge structuredContent."""

    model_config = ConfigDict(extra="forbid")

    action: str
    status: str
    action_id: str | None = None
    sources: dict[str, Any] | None = None
    knowledge: dict[str, Any] | None = None


def get_context_input_json_schema() -> dict:
    schema = GetContextInput.model_json_schema()
    schema["title"] = "get_contextArguments"
    schema["additionalProperties"] = False
    return schema


def get_context_output_json_schema() -> dict:
    schema = GetContextOutput.model_json_schema()
    schema["title"] = "get_contextOutput"
    schema["additionalProperties"] = False
    return schema


def knowledge_input_json_schema() -> dict:
    schema = KnowledgeInput.model_json_schema()
    schema["title"] = "knowledgeArguments"
    schema["additionalProperties"] = False
    return schema


def knowledge_output_json_schema() -> dict:
    schema = KnowledgeOutput.model_json_schema()
    schema["title"] = "knowledgeOutput"
    schema["additionalProperties"] = False
    return schema


class ReadInput(BaseModel):
    """Closed input for semantic reads over governed capabilities."""

    model_config = ConfigDict(extra="forbid")

    capability: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description=(
            "Governed capability id published by get_context "
            "action=catalog/schema — not a free operationId, URL, path, "
            "method or SQL."
        ),
    )
    arguments: dict[str, Any] | None = Field(
        default=None,
        description="Schema-bounded arguments for the capability (see its argument_schema)",
    )


class ReadOutput(BaseModel):
    """Runtime envelope for read structuredContent."""

    model_config = ConfigDict(extra="forbid")

    capability: str
    status: str
    action_id: str
    entity: str | None = None
    shape: str | None = None
    projection: str
    data: Any = None
    truncated: bool
    is_complete: bool
    response_bytes: int | None = None


def read_input_json_schema() -> dict:
    schema = ReadInput.model_json_schema()
    schema["title"] = "readArguments"
    schema["additionalProperties"] = False
    return schema


def read_output_json_schema() -> dict:
    schema = ReadOutput.model_json_schema()
    schema["title"] = "readOutput"
    schema["additionalProperties"] = False
    return schema


class AnalyzeInput(BaseModel):
    """Closed input for governed analyses over analytic-shape capabilities."""

    model_config = ConfigDict(extra="forbid")

    capability: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description=(
            "Governed analytic capability id published by get_context "
            "action=catalog/schema (report/aggregate shapes only)."
        ),
    )
    arguments: dict[str, Any] | None = Field(
        default=None,
        description="Schema-bounded filters/params for the capability",
    )


class AnalyzeOutput(BaseModel):
    """Runtime envelope for analyze structuredContent."""

    model_config = ConfigDict(extra="forbid")

    action: str
    status: str
    capability: str
    facts: dict[str, Any] | None = None
    completeness: dict[str, Any] | None = None
    provenance: dict[str, Any] | None = None
    limitations: list[str] | None = None


def analyze_input_json_schema() -> dict:
    schema = AnalyzeInput.model_json_schema()
    schema["title"] = "analyzeArguments"
    schema["additionalProperties"] = False
    return schema


def analyze_output_json_schema() -> dict:
    schema = AnalyzeOutput.model_json_schema()
    schema["title"] = "analyzeOutput"
    schema["additionalProperties"] = False
    return schema
