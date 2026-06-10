"""Templates e rótulos de respostas humanizadas com dados — bundle humanized_data_response.json."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "humanized_data_response"


class ChatHumanizedDataResponseContentService:
    @classmethod
    def get(cls, *path: str, default: str = "") -> str:
        return ChatAssistantContentService.get(_BUNDLE, *path, default=default)

    @classmethod
    def format(cls, *path: str, default: str = "", **values) -> str:
        return ChatAssistantContentService.format(_BUNDLE, *path, default=default, **values)

    @classmethod
    def list(cls, *path: str) -> list[str]:
        return ChatAssistantContentService.list(_BUNDLE, *path)

    @classmethod
    def get_mapping(cls, *path: str) -> dict[str, str]:
        return ChatAssistantContentService.get_mapping(_BUNDLE, *path)

    @classmethod
    def get_node(cls, *path: str):
        return ChatAssistantContentService.get_node(_BUNDLE, *path)

    @classmethod
    def recommendation_queries(cls, profile_key: str) -> list[dict[str, str]]:
        node = cls.get_node("recommendationQueries", str(profile_key or "").strip())

        if not isinstance(node, list):
            return []

        queries: list[dict[str, str]] = []

        for item in node:
            if not isinstance(item, dict):
                continue

            label = str(item.get("label") or "").strip()
            query = str(item.get("query") or "").strip()

            if not label or not query:
                continue

            queries.append(
                {
                    "label": label,
                    "query": query,
                    "reason": str(item.get("reason") or "").strip(),
                }
            )

        return queries
