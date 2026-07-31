"""Use case fino: NL → sugestões de rotas operacionais (dry-run)."""

from __future__ import annotations


class SuggestOperationalRoutesUseCase:
    def __init__(self, suggestion_service) -> None:
        self.suggestion_service = suggestion_service

    def execute(
        self,
        query: str,
        *,
        limit: int = 5,
        allowed_action_ids: list[str] | None = None,
    ) -> dict:
        suggestions = self.suggestion_service.suggest(
            query,
            limit=limit,
            allowed_action_ids=allowed_action_ids,
        )
        return {
            "ok": True,
            "query": str(query or "").strip(),
            "suggestions": suggestions,
            "total": len(suggestions),
        }
