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

It deliberately does NOT contain (per the design freeze):

- server factories or server-class abstractions;
- auth middleware or ASGI glue (S2–S3);
- identity bridge or error adapter helpers (S4–S5);
- any domain knowledge, tool registry, or business semantics.

Dependency direction: ``delpi_mcp`` may depend on ``delpi_auth``; never on
``tv_app`` / ``tm_app`` / ``app.*`` domain namespaces.
"""

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
    "DELPI_MCP_PROTOCOL_MINIMUM",
    "GateResult",
    "MCP_TRANSPORT_SCOPES",
    "MCP_WWW_AUTHENTICATE_META_KEY",
    "McpConformanceConfig",
    "McpResourceConfig",
    "ValidationIssue",
    "ValidationLayer",
    "build_protected_resource_metadata",
    "build_www_authenticate_challenge",
    "build_www_authenticate_meta",
    "check_protocol_minimum",
    "extract_token_audiences",
    "extract_token_scopes",
    "mcp_allowed_hosts_and_origins",
    "mcp_metadata_router",
    "missing_required_scopes",
    "protected_resource_metadata_url",
    "run_mcp_conformance",
    "token_has_required_audience",
    "validate_tool_wire",
    "validate_tools_wire",
]
