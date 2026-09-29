"""DELPI shared MCP platform foundation (S0 — conformance only).

This package currently contains ONLY the conformance layer:

- ``tool_validation``: wire-level validation of serialized MCP tool
  definitions (reserved ``_meta`` keys, schema shapes, DELPI namespaces).
- ``protocol``: protocol-version policy primitives (platform minimum and
  legacy-migration handling for the VISTA 2026-07-28 incident class).
- ``conformance``: reusable conformance config/report/runner consumed by
  each app's own test suite.

It deliberately does NOT contain (per the design freeze):

- server factories or server-class abstractions;
- auth middleware, resource metadata, ASGI glue (S1–S3);
- identity bridge or error adapter helpers (S4–S5);
- any domain knowledge, tool registry, or business semantics.

Dependency direction: ``delpi_mcp`` may depend on ``delpi_auth``; never on
``tv_app`` / ``tm_app`` / ``app.*`` domain namespaces.
"""

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
    "McpConformanceConfig",
    "ValidationIssue",
    "ValidationLayer",
    "check_protocol_minimum",
    "run_mcp_conformance",
    "validate_tool_wire",
    "validate_tools_wire",
]
