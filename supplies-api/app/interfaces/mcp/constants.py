"""SURI MCP contract constants (semantic contract freeze rev.3).

Technical ids are not branding — «SURI» is product identity; the technical
ids stay ``supplies`` / ``mcp-supplies``.

Semantic surface: exactly five tools (``get_context``, ``read``,
``analyze``, ``knowledge``, ``execute``). Discriminators
(``entity``/``action``/``analysis``) are closed enums validated by the
semantic registry below — never arbitrary strings, URLs or methods.
"""

from __future__ import annotations

# Keycloak confidential client candidate for the SURI MCP surface
# (handoff only — never registered by this codebase).
MCP_PREDEFINED_CLIENT_ID = "mcp-supplies"

CANONICAL_MCP_RESOURCE_URL = "https://minhadelpi.com.br/apps/supplies-api/mcp"

MCP_GATEWAY_ROOT = "/apps/supplies-api"

MCP_AUTH_MODEL = "TRANSPORT_REQUIRES_OAUTH"

# Catalog contract version — bumped on tool surface or wire envelope
# changes (rev.1 = 8 endpoint-oriented tools; rev.2 = 4 semantic tools;
# rev.3 = governed execute for suppliers create/update;
# rev.4 = suppliers reads + postal lookup + creation preview analysis;
# rev.5 = purchase_requests reads + export datasets for SC/PO —
# DECISION-G1 closed: export returns the canonical filtered JSON dataset,
# not binary/base64 — file materialization stays on the BFF/Portal).
CATALOG_VERSION = 5

# DISCOVERY | READ | ANALYSIS | ACT — frozen semantic tool classes.
# Metadata describes semantics; it NEVER authorizes execution.
TOOL_CLASS: dict[str, str] = {
    "get_context": "DISCOVERY",
    "read": "READ",
    "analyze": "ANALYSIS",
    "knowledge": "READ",
    "execute": "ACT",
}

MCP_TOOL_NAMES: tuple[str, ...] = tuple(TOOL_CLASS.keys())

# Supplier create/update are governed non-destructive writes — `delete`
# stays a documented TARGET family, never registered until a real
# contract and authorization exist.
DESTRUCTIVE_ACT_TOOLS: frozenset[str] = frozenset()

# Pagination/scan budgets (rev.1 §3 — unchanged).
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 25
MAX_SAMPLE_SIZE = 100
DEFAULT_SAMPLE_SIZE = 50
MAX_KNOWLEDGE_LIMIT = 20
DEFAULT_KNOWLEDGE_LIMIT = 8

# Governed write budgets — batch writes are bounded and sequential.
MAX_EXECUTE_OPERATIONS = 10
MAX_IDEMPOTENCY_KEY_LENGTH = 128
# Durable idempotency-claim retention for execute keys — the atomic
# claim row lives in supplies.suri_execute_operations (V005) so replays
# survive process restarts and concurrent workers; expired rows are
# garbage-collected lazily on claim.
EXECUTE_IDEMPOTENCY_TTL_HOURS = 24

# ---------------------------------------------------------------------------
# Semantic registry — the ONLY executable capability surface of V1.
#
# Adding a capability = contract + owner authorization + handler + tests,
# never a new tool by default. FUTURE entities (purchase_requests,
# deliveries, inventory, suppliers) must NOT appear here until homologated.
# ---------------------------------------------------------------------------

# Governed reads — closed (entity, action) registry, same style as
# EXECUTE_ACTIONS_BY_ENTITY. Each pair maps to a dedicated handler that
# reuses the canonical BFF service/gateway — no new entity without owner
# contract + tests.
READ_ACTIONS_BY_ENTITY: dict[str, frozenset[str]] = {
    "purchase_orders": frozenset({"search", "get", "export"}),
    "purchase_requests": frozenset(
        {
            "search",
            "summary",
            "requesters",
            "cost_centers",
            "get",
            "export",
        }
    ),
    "suppliers": frozenset(
        {
            "search",
            "get",
            "catalogs",
            "search_by_tax_id",
            "existing",
            "operations",
            "integration_status",
        }
    ),
    "postal_codes": frozenset({"lookup"}),
}
READ_ENTITIES: frozenset[str] = frozenset(READ_ACTIONS_BY_ENTITY)
ANALYSIS_KINDS: frozenset[str] = frozenset(
    {"purchase_orders_summary", "supplier_creation_preview"}
)
KNOWLEDGE_ACTIONS: frozenset[str] = frozenset({"search", "get", "sources"})
CONTEXT_ACTIONS: frozenset[str] = frozenset({"context", "catalog"})

# Governed writes — closed (entity, action) registry. Each pair maps to a
# dedicated handler in supplier_execute; there is no generic executor and
# no arbitrary URL/method/handler selection.
EXECUTE_ACTIONS_BY_ENTITY: dict[str, frozenset[str]] = {
    "suppliers": frozenset({"create", "update"}),
}
EXECUTE_ENTITIES: frozenset[str] = frozenset(EXECUTE_ACTIONS_BY_ENTITY)

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

# PO export shares the search vocabulary minus pagination (BFF contract:
# export ignores page/page_size and returns the full filtered dataset).
PO_EXPORT_FILTER_KEYS: frozenset[str] = PO_SEARCH_FILTER_KEYS - {
    "page",
    "page_size",
}

# Purchase requests (SC) vocabularies — closed mirrors of the
# purchase-requests-api query contracts consumed by the BFF routes.
PR_SEARCH_FILTER_KEYS: frozenset[str] = frozenset(
    {
        "branch",
        "date_from",
        "date_to",
        "request_number",
        "requester_user_id",
        "cost_center",
        "product_code",
        "supplier_code",
        "order_number",
        "overall_stage",
        "sort_by",
        "sort_dir",
        "page",
        "page_size",
    }
)
# Summary accepts the same filter set minus sort/page (PR-api summary
# ignores sort fields and never paginates).
PR_SUMMARY_FILTER_KEYS: frozenset[str] = PR_SEARCH_FILTER_KEYS - {
    "sort_by",
    "sort_dir",
    "page",
    "page_size",
}
# Requesters facet — the PR-api facet contract has no requester_user_id
# or overall_stage keys.
PR_REQUESTERS_FILTER_KEYS: frozenset[str] = frozenset(
    {
        "branch",
        "date_from",
        "date_to",
        "request_number",
        "cost_center",
        "product_code",
        "supplier_code",
        "order_number",
    }
)
# Cost-centers facet — no cost_center/self-filter keys upstream.
PR_COST_CENTERS_FILTER_KEYS: frozenset[str] = frozenset(
    {
        "branch",
        "date_from",
        "date_to",
        "request_number",
        "product_code",
        "supplier_code",
        "order_number",
    }
)
# SC detail context filters (optional facet-scoped lookup params the
# PR-api detail endpoint accepts alongside the path identity).
PR_DETAIL_FILTER_KEYS: frozenset[str] = frozenset(
    {"date_from", "date_to", "cost_center"}
)
PR_GET_IDENTITY_KEYS: frozenset[str] = frozenset(
    {"branch", "request_number"}
)
# SC export — search vocabulary minus pagination (full filtered dataset).
PR_EXPORT_FILTER_KEYS: frozenset[str] = PR_SEARCH_FILTER_KEYS - {
    "page",
    "page_size",
}

# Suppliers read vocabularies — closed mirrors of the BFF query/identity
# contracts (suppliers_routes + supplier_creation_routes).
SUPPLIER_SEARCH_FILTER_KEYS: frozenset[str] = frozenset(
    {
        "query",
        "state",
        "blocked",
        "page",
        "page_size",
        "sort_by",
        "sort_dir",
    }
)
SUPPLIER_GET_IDENTITY_KEYS: frozenset[str] = frozenset(
    {"supplier_code", "supplier_store"}
)
SUPPLIER_CATALOG_FILTER_KEYS: frozenset[str] = frozenset(
    {"kind", "query", "state", "code", "limit"}
)
SUPPLIER_TAX_ID_FILTER_KEYS: frozenset[str] = frozenset(
    {"tax_id", "page", "page_size"}
)
SUPPLIER_OPERATION_IDENTITY_KEYS: frozenset[str] = frozenset({"operation_id"})
POSTAL_CODE_IDENTITY_KEYS: frozenset[str] = frozenset({"postal_code"})
SUPPLIER_PREVIEW_FILTER_KEYS: frozenset[str] = frozenset({"tax_id"})

# Catalog limit and existing-suppliers page caps live with the canonical
# supplier contract owner (suppliers_dto) — consumers import from there.

# Closed per-operation keys for execute(entity=suppliers) — mirrors the
# SupplierWriteOperation schema; unknown keys are rejected in depth.
SUPPLIER_WRITE_OPERATION_KEYS: frozenset[str] = frozenset(
    {
        "idempotency_key",
        "supplier_code",
        "supplier_store",
        "supplier",
        "fields",
    }
)

SEMANTIC_CAPABILITIES: dict[str, dict] = {
    "get_context": {"actions": sorted(CONTEXT_ACTIONS)},
    "read": {
        "entities": {
            entity: {"actions": sorted(actions)}
            for entity, actions in READ_ACTIONS_BY_ENTITY.items()
        },
    },
    "analyze": {"analyses": sorted(ANALYSIS_KINDS)},
    "knowledge": {"actions": sorted(KNOWLEDGE_ACTIONS)},
    "execute": {
        "entities": {
            entity: {"actions": sorted(actions)}
            for entity, actions in EXECUTE_ACTIONS_BY_ENTITY.items()
        },
    },
}
