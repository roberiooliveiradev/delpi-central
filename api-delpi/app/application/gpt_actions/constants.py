"""Frozen V1 constants for api-delpi Custom GPT Actions (004A.2)."""

from __future__ import annotations

GPT_ACTIONS_BASE_PATH = "/gpt-actions/v1"
GPT_ACTIONS_GATEWAY_ROOT = "/apps/api-delpi"
GPT_ACTIONS_PUBLIC_FALLBACK_ORIGIN = "https://minhadelpi.com.br"

# Imported schema operationIds (openapi.json HTTP id stays outside paths).
GPT_ACTIONS_OPERATION_IDS: tuple[str, ...] = (
    "gpt_get_catalog",
    "gpt_search_products",
)
GPT_ACTIONS_SCHEMA_HTTP_OPERATION_ID = "gpt_get_openapi_schema"

GPT_PRODUCT_SEARCH_MAX_PAGE_SIZE = 50
GPT_PRODUCT_SEARCH_DEFAULT_PAGE_SIZE = 50

# Organizational allowlist (004A.2). Maps GPT field → internal search item key.
GPT_SEARCH_FIELD_MAP: dict[str, str] = {
    "product_code": "code",
    "description": "description",
    "group_category": "group_code",
}
GPT_SEARCH_RESPONSE_FIELDS: tuple[str, ...] = tuple(GPT_SEARCH_FIELD_MAP.keys())

# customer_reference and every other Product DTO field remain DENY_BY_DEFAULT.
GPT_SEARCH_DENIED_QUERY_PARAMS: frozenset[str] = frozenset({"customer_reference"})
