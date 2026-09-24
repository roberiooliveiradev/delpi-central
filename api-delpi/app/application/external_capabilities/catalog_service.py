"""Legacy GPT Actions catalog payload (no raw RBAC disclosure)."""

from __future__ import annotations

from typing import Any

from app.application.external_capabilities.constants import (
    PRODUCT_SEARCH_DEFAULT_PAGE_SIZE,
    PRODUCT_SEARCH_MAX_PAGE_SIZE,
    PRODUCT_SEARCH_RESPONSE_FIELDS,
)
from app.application.external_capabilities.davi_agent_intelligence_service import (
    DaviAgentIntelligenceService,
)
from app.application.external_capabilities.product_search_auth import (
    user_can_search_products,
)
from app.application.gpt_actions.constants import GPT_ACTIONS_OPERATION_IDS


def build_gpt_catalog() -> dict[str, Any]:
    """Describe V1 GPT capabilities. Availability is AuthZ-derived; codes stay internal."""
    can_search = user_can_search_products()
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
            "description": "Search products with minimal Product Master projection.",
            "responseFields": list(PRODUCT_SEARCH_RESPONSE_FIELDS),
            "deniedFieldsNote": (
                "customer_reference and all other product fields are deny-by-default."
            ),
            "queryParams": ["code", "description", "group_code", "page", "page_size"],
            "pagination": {
                "defaultPageSize": PRODUCT_SEARCH_DEFAULT_PAGE_SIZE,
                "maxPageSize": PRODUCT_SEARCH_MAX_PAGE_SIZE,
            },
        },
    ]
    return {
        "version": "v1",
        "status": "LEGACY_TRANSITIONAL",
        "strategicTarget": "openai-plugin-mcp",
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
        "capability_surface": DaviAgentIntelligenceService.capability_surface(),
        "limitations": [
            "V1 exposes product search projection only.",
            "Stock, BOM, production, pricing, finance and sales are out of scope.",
            "New DTO fields remain blocked until explicit organizational approval.",
            "Do not paginate autonomously without bound; max page_size is 50.",
            "Strategic external target is OpenAI Plugin + MCP; this surface is transitional.",
            "Obey capability_surface.agent_directives for live READ operational posture.",
        ],
    }
