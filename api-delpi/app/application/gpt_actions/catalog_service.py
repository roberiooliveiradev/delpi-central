"""Catalog payload for api-delpi Custom GPT Actions V1."""

from __future__ import annotations

from typing import Any

from delpi_auth.authz_core import has_any_permission
from delpi_auth.request_context import get_current_user

from app.application.gpt_actions.constants import (
    GPT_ACTIONS_OPERATION_IDS,
    GPT_PRODUCT_SEARCH_DEFAULT_PAGE_SIZE,
    GPT_PRODUCT_SEARCH_MAX_PAGE_SIZE,
    GPT_SEARCH_RESPONSE_FIELDS,
)
from app.application.security.api_delpi_permissions import ENGINEERING_LMP_ACCESS


def _user_can_search_products() -> bool:
    user = get_current_user()
    if user is None:
        return False
    return has_any_permission(user, ENGINEERING_LMP_ACCESS)


def build_gpt_catalog() -> dict[str, Any]:
    """Describe V1 capabilities. AuthZ-derived availability — not a parallel matrix."""
    can_search = _user_can_search_products()
    capabilities = [
        {
            "operationId": "gpt_get_catalog",
            "available": True,
            "readOnly": True,
            "description": "List V1 capabilities, enums, field allowlist and limits.",
        },
        {
            "operationId": "gpt_search_products",
            "available": can_search,
            "readOnly": True,
            "requiredPermissionAnyOf": list(ENGINEERING_LMP_ACCESS),
            "description": "Search products with minimal Product Master projection.",
            "responseFields": list(GPT_SEARCH_RESPONSE_FIELDS),
            "deniedFieldsNote": (
                "customer_reference and all other product fields are deny-by-default."
            ),
            "queryParams": ["code", "description", "group_code", "page", "page_size"],
            "pagination": {
                "defaultPageSize": GPT_PRODUCT_SEARCH_DEFAULT_PAGE_SIZE,
                "maxPageSize": GPT_PRODUCT_SEARCH_MAX_PAGE_SIZE,
            },
        },
    ]
    return {
        "version": "v1",
        "readOnly": True,
        "surface": "api-delpi-gpt-actions",
        "approvalReference": "API-DELPI-GPT-004A.2",
        "dataClassification": "INTERNAL",
        "externalProcessing": "APPROVED_WITH_RESTRICTIONS",
        "operationIds": list(GPT_ACTIONS_OPERATION_IDS),
        "capabilities": capabilities,
        "allowedCapabilities": [
            item["operationId"] for item in capabilities if item.get("available")
        ],
        "limitations": [
            "V1 exposes product search projection only.",
            "Stock, BOM, production, pricing, finance and sales are out of scope.",
            "New DTO fields remain blocked until explicit organizational approval.",
            "Do not paginate autonomously without bound; max page_size is 50.",
        ],
    }
