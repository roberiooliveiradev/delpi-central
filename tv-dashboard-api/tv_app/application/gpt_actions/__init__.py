"""TV Dashboard Custom GPT Actions — owner-local package."""

from __future__ import annotations

GPT_ACTIONS_BASE_PATH = "/gpt-actions/v1"
GPT_ACTIONS_GATEWAY_ROOT = "/apps/tv-dashboard-api"
GPT_ACTIONS_PUBLIC_FALLBACK_ORIGIN = "https://minhadelpi.com.br"
GPT_COMMIT_OPERATION = "vista_execute"

GPT_ACTIONS_OPERATION_IDS: tuple[str, ...] = (
    # SIX-TOOLS-ONLY consolidation — one Action per semantic verb.
    "vista_get_context",
    "vista_read",
    "vista_analyze",
    "vista_knowledge",
    "vista_execute",
    "vista_delete",
)

GPT_ACTIONS_SCHEMA_HTTP_OPERATION_ID = "gpt_get_openapi_schema"

CUSTOM_GPT_CORS_ORIGINS: tuple[str, ...] = (
    "https://chatgpt.com",
    "https://chat.openai.com",
)
