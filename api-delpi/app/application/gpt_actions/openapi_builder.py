"""Build compact OpenAPI 3.1 schema for OpenAI Custom GPT Actions import."""

from __future__ import annotations

from typing import Any

from app.application.gpt_actions.constants import (
    GPT_ACTIONS_BASE_PATH,
    GPT_ACTIONS_GATEWAY_ROOT,
    GPT_ACTIONS_OPERATION_IDS,
    GPT_ACTIONS_PUBLIC_FALLBACK_ORIGIN,
    GPT_PRODUCT_SEARCH_DEFAULT_PAGE_SIZE,
    GPT_PRODUCT_SEARCH_MAX_PAGE_SIZE,
    GPT_SEARCH_RESPONSE_FIELDS,
)


def resolve_gpt_actions_server_url(
    *,
    public_base_url: str | None = None,
    root_path: str | None = None,
    explicit: str | None = None,
) -> str:
    if explicit and str(explicit).startswith(("http://", "https://")):
        return str(explicit).rstrip("/")
    root = (root_path or GPT_ACTIONS_GATEWAY_ROOT).strip() or GPT_ACTIONS_GATEWAY_ROOT
    if not root.startswith("/"):
        root = f"/{root}"
    root = root.rstrip("/") or GPT_ACTIONS_GATEWAY_ROOT
    base = (public_base_url or "").rstrip("/")
    if base.startswith(("http://", "https://")):
        return f"{base}{root}"
    return f"{GPT_ACTIONS_PUBLIC_FALLBACK_ORIGIN}{root}"


def build_gpt_actions_openapi(
    *,
    public_base_url: str | None = None,
    root_path: str | None = None,
) -> dict[str, Any]:
    server_url = resolve_gpt_actions_server_url(
        public_base_url=public_base_url,
        root_path=root_path,
    )
    base = GPT_ACTIONS_BASE_PATH
    bearer = [{"BearerAuth": []}]
    product_item = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "product_code": {"type": "string", "description": "Product code (B1_COD)."},
            "description": {"type": "string", "description": "Product description."},
            "group_category": {
                "type": "string",
                "description": "Product group code (mapped from group_code).",
            },
        },
        "required": list(GPT_SEARCH_RESPONSE_FIELDS),
    }
    envelope = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"},
            "data": {"type": "object"},
            "error": {"type": ["object", "null"]},
            "meta": {"type": "object"},
        },
    }
    return {
        "openapi": "3.1.1",
        "info": {
            "title": "API DELPI GPT Actions V1",
            "version": "1.0.0",
            "description": (
                "Compact READ-ONLY facade for Custom GPT. "
                "Approval: API-DELPI-GPT-004A.2. AuthZ remains backend ENGINEERING_LMP_ACCESS."
            ),
        },
        "servers": [{"url": server_url}],
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": (
                        "Keycloak access token from OAuth Authorization Code "
                        "(client chatgpt-api-delpi). Audience must include delpi-central."
                    ),
                }
            },
            "schemas": {
                "ApiDelpiEnvelope": envelope,
                "GptProductSearchItem": product_item,
            },
        },
        "paths": {
            f"{base}/catalog": {
                "get": {
                    "operationId": "gpt_get_catalog",
                    "summary": "List V1 GPT capabilities and field allowlist",
                    "description": (
                        "Returns read-only catalog, allowedCapabilities from AuthZ, "
                        "and Product Master field allowlist."
                    ),
                    "security": bearer,
                    "responses": {
                        "200": {
                            "description": "Catalog payload",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ApiDelpiEnvelope"}
                                }
                            },
                        },
                        "401": {"description": "Unauthorized"},
                        "403": {"description": "Forbidden"},
                    },
                }
            },
            f"{base}/products/search": {
                "get": {
                    "operationId": "gpt_search_products",
                    "summary": "Search products with minimal projection",
                    "description": (
                        "Searches products via existing use case. Returns only "
                        "product_code, description, group_category. page_size max 50."
                    ),
                    "security": bearer,
                    "parameters": [
                        {
                            "name": "code",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                            "description": "Product code filter (partial/exact per backend).",
                        },
                        {
                            "name": "description",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                            "description": "Description filter.",
                        },
                        {
                            "name": "group_code",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                            "description": "Product group filter (group_category source).",
                        },
                        {
                            "name": "page",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "minimum": 1, "default": 1},
                        },
                        {
                            "name": "page_size",
                            "in": "query",
                            "required": False,
                            "schema": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": GPT_PRODUCT_SEARCH_MAX_PAGE_SIZE,
                                "default": GPT_PRODUCT_SEARCH_DEFAULT_PAGE_SIZE,
                            },
                            "description": f"Max {GPT_PRODUCT_SEARCH_MAX_PAGE_SIZE}.",
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "Paged projected products",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ApiDelpiEnvelope"}
                                }
                            },
                        },
                        "401": {"description": "Unauthorized"},
                        "403": {"description": "Forbidden"},
                    },
                }
            },
        },
        "x-delpi-gpt-actions": {
            "status": "LEGACY_TRANSITIONAL",
            "strategicTarget": "openai-plugin-mcp",
            "importedOperationIds": list(GPT_ACTIONS_OPERATION_IDS),
            "schemaHttpOperationId": "gpt_get_openapi_schema",
            "note": (
                "openapi.json path is public for import but omitted from paths. "
                "Strategic external integration is OpenAI Plugin + MCP."
            ),
        },
    }
