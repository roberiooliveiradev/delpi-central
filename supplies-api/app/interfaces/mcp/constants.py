"""SURI MCP contract constants (semantic contract freeze rev.2).

Technical ids are not branding — «SURI» is product identity; the technical
ids stay ``supplies`` / ``mcp-supplies``.

Semantic surface: exactly four tools (``get_context``, ``read``,
``analyze``, ``knowledge``). Discriminators (``entity``/``action``/
``analysis``) are closed enums validated by the semantic registry below —
never arbitrary strings, URLs or methods.
"""

from __future__ import annotations

# Keycloak confidential client candidate for the SURI MCP surface
# (handoff only — never registered by this codebase).
MCP_PREDEFINED_CLIENT_ID = "mcp-supplies"

CANONICAL_MCP_RESOURCE_URL = "https://minhadelpi.com.br/apps/supplies-api/mcp"

MCP_GATEWAY_ROOT = "/apps/supplies-api"

MCP_AUTH_MODEL = "TRANSPORT_REQUIRES_OAUTH"

# Catalog contract version — bumped on tool surface or wire envelope
# changes (rev.1 = 8 endpoint-oriented tools; rev.2 = 4 semantic tools).
CATALOG_VERSION = 2

# DISCOVERY | READ | ANALYSIS — frozen semantic tool classes. Metadata
# describes semantics; it NEVER authorizes execution.
TOOL_CLASS: dict[str, str] = {
    "get_context": "DISCOVERY",
    "read": "READ",
    "analyze": "ANALYSIS",
    "knowledge": "READ",
}

MCP_TOOL_NAMES: tuple[str, ...] = tuple(TOOL_CLASS.keys())

# No ACT/PREPARE tools in V1 — the entire surface is read-only.
# `execute` and `delete` are documented TARGET families (handoff/plan),
# never registered until real contracts and authorization exist.
DESTRUCTIVE_ACT_TOOLS: frozenset[str] = frozenset()

# Pagination/scan budgets (rev.1 §3 — unchanged).
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 25
MAX_SAMPLE_SIZE = 100
DEFAULT_SAMPLE_SIZE = 50
MAX_KNOWLEDGE_LIMIT = 20
DEFAULT_KNOWLEDGE_LIMIT = 8

# ---------------------------------------------------------------------------
# Semantic registry — the ONLY executable capability surface of V1.
#
# Adding a capability = contract + owner authorization + handler + tests,
# never a new tool by default. FUTURE entities (purchase_requests,
# deliveries, inventory, suppliers) must NOT appear here until homologated.
# ---------------------------------------------------------------------------

READ_ENTITIES: frozenset[str] = frozenset({"purchase_orders"})
READ_ACTIONS: frozenset[str] = frozenset({"search", "get"})
ANALYSIS_KINDS: frozenset[str] = frozenset({"purchase_orders_summary"})
KNOWLEDGE_ACTIONS: frozenset[str] = frozenset({"search", "get", "sources"})
CONTEXT_ACTIONS: frozenset[str] = frozenset({"context", "catalog"})

# Closed filter vocabularies — unknown keys are rejected (422), never
# forwarded, so no arbitrary field can bypass the owner contract.
PO_SEARCH_FILTER_KEYS: frozenset[str] = frozenset(
    {
        "branch",
        "order_number",
        "product_code",
        "supplier_code",
        "expected_delivery_from",
        "expected_delivery_to",
        "late_only",
        "sort_by",
        "sort_dir",
        "page",
        "page_size",
    }
)

PO_ANALYZE_FILTER_KEYS: frozenset[str] = frozenset(
    {
        "branch",
        "order_number",
        "product_code",
        "supplier_code",
        "expected_delivery_from",
        "expected_delivery_to",
        "late_only",
    }
)

PO_GET_IDENTITY_KEYS: frozenset[str] = frozenset({"branch", "order_number"})

SEMANTIC_CAPABILITIES: dict[str, dict] = {
    "get_context": {"actions": sorted(CONTEXT_ACTIONS)},
    "read": {
        "entities": {
            "purchase_orders": {"actions": sorted(READ_ACTIONS)},
        },
    },
    "analyze": {"analyses": sorted(ANALYSIS_KINDS)},
    "knowledge": {"actions": sorted(KNOWLEDGE_ACTIONS)},
}
