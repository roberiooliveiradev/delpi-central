"""DELPI shared MCP platform foundation (S0 — conformance only).

This package currently contains ONLY the conformance layer:

- ``tool_validation``: wire-level validation of serialized MCP tool
  definitions (reserved ``_meta`` keys, schema shapes, DELPI namespaces).
- ``protocol``: protocol-version policy primitives (platform minimum and
  legacy-migration handling for the VISTA 2026-07-28 incident class).
- ``conformance``: reusable conformance config/report/runner consumed by
  each app's own test suite.
- ``resource_contract`` (S1): MCP transport-facing OAuth + RFC 9728
  protected-resource contract — challenge/scope/audience helpers, metadata
  document builder and route factory, ``mcp/www_authenticate`` envelope.
- ``transport`` (S2): canonical ``/mcp`` path rewrite middleware, lifespan
  composition, and the DNS-rebinding-enabled transport-security shape.
- ``auth`` (S3): MCP transport AuthN gate — Bearer/audience/scope checks
  composing ``delpi_auth`` (never reimplementing it), plus the shared
  ``/mcp`` data-path predicate.
- ``identity`` (S4): read-only snapshot of the delpi_auth-established
  context and the minimal Starlette Request bridge for adapters.
- ``errors`` / ``tool_metadata`` (S5): SDK-tolerant CallToolResult wire
  assembly, HTTP-status→kind vocabulary, detail redaction, and the frozen
  DELPI ToolClass/annotation/meta vocabulary. Envelope shapes and domain
  error mapping remain app-owned.

It deliberately does NOT contain (per the design freeze):

- server factories or server-class abstractions;
- domain error types or domain-specific exception mapping;
- any domain knowledge, tool registry, or business semantics.

Dependency direction: ``delpi_mcp`` may depend on ``delpi_auth``; never on
``tv_app`` / ``tm_app`` / ``app.*`` domain namespaces.
"""

from .auth import (
    McpTransportAuthPolicy,
    is_mcp_data_path,
    mcp_transport_auth,
)
from .errors import (
    INTERNAL_ERROR_MESSAGE,
    json_payload_text,
    kind_for_http_status,
    mcp_tool_result,
    redact_error_details,
)
from .identity import (
    McpRequestContext,
    build_mcp_request,
    current_mcp_context,
    require_mcp_context,
)
from .tool_metadata import (
    DELPI_META_SECURITY_SCHEMES,
    DELPI_META_TOOL_CLASS,
    SECURITY_SCHEMES_KEY,
    TOOL_CLASS_ACT,
    TOOL_CLASS_ANALYSIS,
    TOOL_CLASS_PREPARE,
    TOOL_CLASS_READ,
    delpi_tool_meta,
    security_schemes_meta,
    tool_annotations_payload,
)
from .resource_contract import (
    MCP_TRANSPORT_SCOPES,
    MCP_WWW_AUTHENTICATE_META_KEY,
    McpResourceConfig,
    build_protected_resource_metadata,
    build_www_authenticate_challenge,
    build_www_authenticate_meta,
    extract_token_audiences,
    extract_token_scopes,
    mcp_allowed_hosts_and_origins,
    mcp_metadata_router,
    missing_required_scopes,
    protected_resource_metadata_url,
    token_has_required_audience,
)
from .transport import (
    combine_lifespans,
    mcp_mount_path_middleware,
    mcp_transport_security_settings,
    normalize_mcp_mount_path,
)
from .conformance import (
    ConformanceReport,
    ConformanceStatus,
    GateResult,
    McpConformanceConfig,
    run_mcp_conformance,
)
from .protocol import (
    DELPI_MCP_PROTOCOL_MINIMUM,
    check_protocol_minimum,
)
from .tool_validation import (
    ValidationIssue,
    ValidationLayer,
    validate_tool_wire,
    validate_tools_wire,
)

__all__ = [
    "ConformanceReport",
    "ConformanceStatus",
    "DELPI_META_SECURITY_SCHEMES",
    "DELPI_META_TOOL_CLASS",
    "DELPI_MCP_PROTOCOL_MINIMUM",
    "GateResult",
    "INTERNAL_ERROR_MESSAGE",
    "MCP_TRANSPORT_SCOPES",
    "MCP_WWW_AUTHENTICATE_META_KEY",
    "McpConformanceConfig",
    "McpRequestContext",
    "McpResourceConfig",
    "McpTransportAuthPolicy",
    "SECURITY_SCHEMES_KEY",
    "TOOL_CLASS_ACT",
    "TOOL_CLASS_ANALYSIS",
    "TOOL_CLASS_PREPARE",
    "TOOL_CLASS_READ",
    "ValidationIssue",
    "ValidationLayer",
    "build_mcp_request",
    "build_protected_resource_metadata",
    "build_www_authenticate_challenge",
    "build_www_authenticate_meta",
    "check_protocol_minimum",
    "combine_lifespans",
    "current_mcp_context",
    "delpi_tool_meta",
    "extract_token_audiences",
    "extract_token_scopes",
    "is_mcp_data_path",
    "json_payload_text",
    "kind_for_http_status",
    "mcp_allowed_hosts_and_origins",
    "mcp_metadata_router",
    "mcp_mount_path_middleware",
    "mcp_tool_result",
    "mcp_transport_auth",
    "mcp_transport_security_settings",
    "missing_required_scopes",
    "normalize_mcp_mount_path",
    "require_mcp_context",
    "protected_resource_metadata_url",
    "redact_error_details",
    "run_mcp_conformance",
    "security_schemes_meta",
    "token_has_required_audience",
    "tool_annotations_payload",
    "validate_tool_wire",
    "validate_tools_wire",
]
