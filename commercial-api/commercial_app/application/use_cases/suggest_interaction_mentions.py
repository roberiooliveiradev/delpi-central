from __future__ import annotations

from typing import Any, Protocol, Sequence

from commercial_app.domain.services.interaction_mention_kinds_content_service import (
    InteractionMentionKindsContentService,
)


class DirectoryUserSearchPort(Protocol):
    def search_directory_users(
        self,
        *,
        query: str | None = None,
        limit: int = 20,
        browse: bool = False,
    ) -> list[dict[str, str]]:
        ...


class SuggestInteractionMentionsUseCase:
    """Sugestões de @ — kinds só do catálogo; user via directory do Core."""

    def __init__(self, directory: DirectoryUserSearchPort) -> None:
        self._directory = directory

    def suggest(
        self,
        *,
        query: str,
        kinds: Sequence[str] | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        requested = [
            str(item).strip()
            for item in (kinds or ("user",))
            if str(item).strip()
        ]
        if not requested:
            requested = ["user"]
        known = InteractionMentionKindsContentService.kind_ids()
        enabled = InteractionMentionKindsContentService.suggest_enabled_ids()
        wanted = [kind for kind in requested if kind in known and kind in enabled]
        items: list[dict[str, Any]] = []
        if "user" in wanted:
            items.extend(
                self._suggest_users(query=query, limit=limit)
            )
        return items

    def _suggest_users(self, *, query: str, limit: int) -> list[dict[str, Any]]:
        users = self._directory.search_directory_users(
            query=query,
            limit=limit,
            browse=not bool((query or "").strip()),
        )
        out: list[dict[str, Any]] = []
        for user in users:
            user_id = str(user.get("id") or "").strip()
            if not user_id:
                continue
            name = str(user.get("name") or user_id).strip()
            email = str(user.get("email") or "").strip()
            out.append(
                {
                    "kind": "user",
                    "label": name,
                    "subtitle": email,
                    "ref": {"user_id": user_id},
                }
            )
        return out
