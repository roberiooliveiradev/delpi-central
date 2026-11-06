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
# not binary/base64 — file materialization stays on the BFF/Portal;
# rev.6 = deliveries.late + inventory summary/items (P1-R3);
# rev.7 = safety_stock filters/summary/items/details/suppliers (R-13/R-14);
# rev.8 = otd aggregate/series + analyze(overview_summary) (R-02/R-03);
# rev.9 = consumption-audit search/get/comparison (R-23..R-25);
# rev.10 = market_intelligence 9 reads + comex products/governance/views (R-26..R-29);
# rev.11 = session capabilities/preferences + users profile/photo/related (R-01,R-30..R-32);
# rev.12 = comex governed writes ncm_request/ncm_transition/view_create/view_update (W-06..W-08);
# rev.13 = enrichment governed writes review_create/decide/decide_bulk/prepare_update (W-03..W-05);
# rev.14 = session preferences_update + users profile_update (W-01, W-02);
# rev.15 = comex view_delete (W-09) — confirmation-required.
# rev.16 = safety_stock closed vocabularies typed on the wire —
# status/branch/sortBy/sortDirection publish the canonical enums the
# BFF owner already enforces (derived, never duplicated).
CATALOG_VERSION = 16

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
    "avatar": frozenset({"get"}),
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
    "deliveries": frozenset({"late"}),
    "inventory": frozenset({"summary", "items"}),
    "safety_stock": frozenset(
        {"filters", "summary", "items", "details", "suppliers"}
    ),
    "otd": frozenset({"aggregate", "series"}),
    "consumption": frozenset({"search", "get", "comparison"}),
    "market": frozenset(
        {
            "filters",
            "summary",
            "series",
            "import_series",
            "producer_price_series",
            "fx_series",
            "quote_series",
            "quote_compare",
            "monthly_averages",
        }
    ),
    "comex": frozenset(
        {
            "products_search",
            "ncm_governance",
            "ncm_governance_get",
            "views",
            "view_get",
        }
    ),
    "session": frozenset({"capabilities", "preferences"}),
    "users": frozenset({"profile", "photo", "related_requests"}),
}
READ_ENTITIES: frozenset[str] = frozenset(READ_ACTIONS_BY_ENTITY)
ANALYSIS_KINDS: frozenset[str] = frozenset(
    {
        "purchase_orders_summary", "supplier_creation_preview",
        "overview_summary", "procurement_diagnostic",
    }
)
KNOWLEDGE_ACTIONS: frozenset[str] = frozenset({"search", "get", "sources"})
CONTEXT_ACTIONS: frozenset[str] = frozenset({"context", "catalog"})

# Governed writes — closed (entity, action) registry. Each pair maps to a
# dedicated handler in supplier_execute; there is no generic executor and
# no arbitrary URL/method/handler selection.
EXECUTE_ACTIONS_BY_ENTITY: dict[str, frozenset[str]] = {
    "suppliers": frozenset({"create", "update"}),
    "comex": frozenset(
        {
            "ncm_request", "ncm_transition", "view_create",
            "view_update", "view_delete",
        }
    ),
    "enrichment": frozenset(
        {"review_create", "decide", "decide_bulk", "prepare_update"}
    ),
    "session": frozenset({"preferences_update"}),
    "users": frozenset({"profile_update"}),
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
# R-11 / R-12 (G3) — closed filter vocabularies, mirrored from the BFF
# routes: deliveries (/deliveries/late) and inventory
# (/inventory/stock-balances/{summary,items}).
DELIVERIES_LATE_FILTER_KEYS: frozenset[str] = frozenset(
    {
        "branch",
        "status",
        "start_date",
        "end_date",
        "sort_by",
        "sort_dir",
        "page",
        "page_size",
    }
)
DELIVERIES_LATE_STATUS: frozenset[str] = frozenset({"late", "on_time"})
DELIVERIES_LATE_SORT_KEYS: frozenset[str] = frozenset(
    {
        "status",
        "branch",
        "order_number",
        "order_item",
        "product_code",
        "product_description",
        "supplier_code",
        "supplier_name",
        "supplier_short_name",
        "expected_delivery_date",
        "receipt_entry_date",
        "quantity",
        "days_diff",
    }
)
INVENTORY_SUMMARY_FILTER_KEYS: frozenset[str] = frozenset(
    {"branch", "warehouse"}
)
INVENTORY_ITEMS_FILTER_KEYS: frozenset[str] = frozenset(
    {"branch", "warehouse", "page", "page_size", "sort"}
)
INVENTORY_ITEMS_SORT_KEYS: frozenset[str] = frozenset(
    {
        "stock_value_desc",
        "stock_value_asc",
        "quantity_desc",
        "quantity_asc",
        "product_code_asc",
        "product_code_desc",
    }
)
INVENTORY_ITEMS_MAX_PAGE_SIZE = 500
DELIVERIES_LATE_MAX_PAGE_SIZE = 1000

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

SAFETY_STOCK_FILTERS_FILTER_KEYS = frozenset({"branch", "includeBlocked"})
SAFETY_STOCK_SUMMARY_FILTER_KEYS = frozenset(
    {"branch", "includeBlocked", "productGroup", "unit", "search",
     "status", "includeWithoutSafetyStock"}
)
SAFETY_STOCK_ITEMS_FILTER_KEYS = SAFETY_STOCK_SUMMARY_FILTER_KEYS | frozenset(
    {"page", "page_size", "sortBy", "sortDirection"}
)
SAFETY_STOCK_ITEM_IDENTITY_KEYS = frozenset({"code", "branch"})

OTD_COMMON_FILTER_KEYS = frozenset({"branch", "start_date", "end_date"})
OTD_AGGREGATE_FILTER_KEYS = frozenset(
    {"branch", "start_date", "end_date"}
)
OTD_SERIES_FILTER_KEYS = frozenset(
    {"branch", "start_date", "end_date", "granularity"}
)
PROCUREMENT_DIAGNOSTIC_FILTER_KEYS = frozenset(
    {"branch", "start_date", "end_date", "include_sections"}
)

OVERVIEW_SUMMARY_FILTER_KEYS = frozenset(
    {"branch", "start_date", "end_date"}
)

CONSUMPTION_SEARCH_FILTER_KEYS = frozenset(
    {
        "unit",
        "search",
        "product",
        "date_type",
        "period_start",
        "period_end",
        "status",
        "work_center",
        "operation",
        "page",
        "page_size",
    }
)
CONSUMPTION_COMPARISON_FILTER_KEYS = frozenset({"unit", "orders"})
CONSUMPTION_IDENTITY_KEYS = frozenset({"unit", "production_order"})
CONSUMPTION_DATE_TYPES = frozenset({"emission", "finished", "appointment"})

MARKET_FILTERS_KEYS = frozenset(set())
MARKET_COMMON_KEYS = frozenset(
    {"instrument", "currency", "fx_kind", "date_from", "date_to"}
)
MARKET_SERIES_KEYS = MARKET_COMMON_KEYS | frozenset({"granularity"})
MARKET_IMPORT_SERIES_KEYS = frozenset(
    {"ncm", "granularity", "date_from", "date_to", "country_code", "state_code"}
)
MARKET_PRODUCER_PRICE_KEYS = frozenset(
    {"series_id", "granularity", "date_from", "date_to"}
)
MARKET_FX_KEYS = frozenset({"fx_kind", "granularity", "date_from", "date_to"})
MARKET_QUOTE_KEYS = frozenset(
    {"instruments", "granularity", "currency", "fx_kind", "date_from", "date_to"}
)
MARKET_MONTHLY_KEYS = MARKET_COMMON_KEYS | frozenset({"page", "page_size"})
COMEX_PRODUCTS_KEYS = frozenset(
    {"code", "description", "product_type", "group_code", "search",
     "page", "page_size"}
)
COMEX_NCM_LIST_KEYS = frozenset({"status"})
COMEX_VIEWS_KEYS = frozenset(set())
COMEX_IDENTITY_KEYS = frozenset({"governance_id", "view_id"})

SESSION_CAPABILITIES_KEYS = frozenset(set())
SESSION_PREFERENCES_KEYS = frozenset(set())
USERS_PROFILE_KEYS = frozenset(set())
USERS_PHOTO_KEYS = frozenset(set())
USERS_RELATED_KEYS = frozenset(
    {"branch", "page", "page_size", "sort_by", "sort_dir"}
)
USERS_IDENTITY_KEYS = frozenset({"user_id"})
