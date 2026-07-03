"""Ferramentas internas da plataforma — nomes canônicos para skip RAG e resposta direta."""

from __future__ import annotations

PLATFORM_INTERNAL_TOOL_NAMES = frozenset(
    {
        "get_current_user",
        "get_allowed_apps",
        "get_allowed_routes",
        "search_knowledge_base",
    }
)

PLATFORM_DIRECT_ANSWER_TOOL_NAMES = frozenset(
    {
        "get_current_user",
        "get_allowed_apps",
        "get_allowed_routes",
    }
)


class ChatPlatformInternalToolsService:
    @classmethod
    def is_platform_internal_tool(cls, tool_name: str | None) -> bool:
        return str(tool_name or "") in PLATFORM_INTERNAL_TOOL_NAMES

    @classmethod
    def is_direct_answer_tool(cls, tool_name: str | None) -> bool:
        return str(tool_name or "") in PLATFORM_DIRECT_ANSWER_TOOL_NAMES

    @classmethod
    def is_platform_direct_answer_turn(cls, tool_calls: list | None) -> bool:
        if not isinstance(tool_calls, list) or len(tool_calls) != 1:
            return False

        return cls.is_direct_answer_tool(str(tool_calls[0].get("name") or ""))
