"""SURI MCP contract constants (S1 freeze).

Technical ids are not branding — «SURI» is product identity; the technical
ids stay ``supplies`` / ``mcp-supplies``.
"""

from __future__ import annotations

# Keycloak confidential client candidate for the SURI MCP surface
# (handoff only — never registered by this codebase).
MCP_PREDEFINED_CLIENT_ID = "mcp-supplies"

CANONICAL_MCP_RESOURCE_URL = "https://minhadelpi.com.br/apps/supplies-api/mcp"

MCP_GATEWAY_ROOT = "/apps/supplies-api"

MCP_AUTH_MODEL = "TRANSPORT_REQUIRES_OAUTH"

# Catalog contract version — bumped when the tool surface or wire
# envelopes change (never on content-only knowledge updates).
CATALOG_VERSION = 1

# DISCOVERY | READ | ANALYSIS — frozen S1 tool classes. Metadata describes
# semantics; it NEVER authorizes execution.
TOOL_CLASS: dict[str, str] = {
    "get_my_context": "READ",
    "get_catalog": "DISCOVERY",
    "list_purchase_orders": "READ",
    "get_purchase_order": "READ",
    "search_supplies_knowledge": "READ",
    "get_knowledge_item": "READ",
    "list_knowledge_sources": "DISCOVERY",
    "analyze_purchase_orders": "ANALYSIS",
}

MCP_TOOL_NAMES: tuple[str, ...] = tuple(TOOL_CLASS.keys())

# No ACT/PREPARE tools in v1 — the entire surface is read-only.
DESTRUCTIVE_ACT_TOOLS: frozenset[str] = frozenset()

# Pagination/scan budgets (S1 §3).
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 25
MAX_SAMPLE_SIZE = 100
DEFAULT_SAMPLE_SIZE = 50
MAX_KNOWLEDGE_LIMIT = 20
DEFAULT_KNOWLEDGE_LIMIT = 8
