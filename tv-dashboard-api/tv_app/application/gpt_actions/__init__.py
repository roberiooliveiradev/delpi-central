"""TV Dashboard Custom GPT Actions — owner-local package."""

from __future__ import annotations

GPT_ACTIONS_BASE_PATH = "/gpt-actions/v1"
GPT_ACTIONS_GATEWAY_ROOT = "/apps/tv-dashboard-api"
GPT_ACTIONS_PUBLIC_FALLBACK_ORIGIN = "https://minhadelpi.com.br"
GPT_COMMIT_OPERATION = "gpt_commit_change"

GPT_ACTIONS_OPERATION_IDS: tuple[str, ...] = (
    "gpt_get_catalog",
    "gpt_list_playlists",
    "gpt_get_playlist_context",
    "gpt_search_data_routes",
    "gpt_preview_data_block",
    "gpt_suggest_change",
    "gpt_preview_change",
    "gpt_commit_change",
)

GPT_ACTIONS_SCHEMA_HTTP_OPERATION_ID = "gpt_get_openapi_schema"

CUSTOM_GPT_CORS_ORIGINS: tuple[str, ...] = (
    "https://chatgpt.com",
    "https://chat.openai.com",
)
