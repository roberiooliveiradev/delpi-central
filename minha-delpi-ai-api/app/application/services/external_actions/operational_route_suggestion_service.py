"""Sugestão dry-run de rotas operacionais (sem execute_external_action)."""

from __future__ import annotations

from app.application.services.external_actions.external_action_selection_support_service import (
    ExternalActionSelectionSupportService,
)
from app.domain.services.chat_operational_api_domain_service import (
    ChatOperationalApiDomainService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class OperationalRouteSuggestionService:
    """Rankeia candidatos do catálogo OpenAPI para descoberta cross-app (ex.: TV)."""

    def __init__(self, repository, *, semantic_ranker=None) -> None:
        self.repository = repository
        self._support = ExternalActionSelectionSupportService(
            repository,
            semantic_ranker=semantic_ranker,
        )

    def suggest(
        self,
        query: str,
        *,
        limit: int = 5,
        allowed_action_ids: list[str] | None = None,
        provider_key: str = "api-delpi",
    ) -> list[dict]:
        message = str(query or "").strip()
        if not message:
            return []

        cap = max(1, min(int(limit or 5), 20))
        allowed = allowed_action_ids
        if allowed is None:
            allowed = [
                str(action.get("actionId") or "")
                for action in self.repository.list_actions(provider_key=provider_key)
                if action.get("actionId")
            ]

        if not allowed:
            return []

        pool_limit = max(80, cap * 8)
        candidates = self._support.list_allowed_candidates(
            message,
            allowed_action_ids=allowed,
            limit=pool_limit,
        )
        ranked = self._support.rank_candidates(
            message,
            candidates,
            allowed_action_ids=allowed,
        )

        out: list[dict] = []
        seen: set[str] = set()
        for action in ranked:
            operation_id = str(action.get("operationId") or "").strip()
            action_id = str(action.get("actionId") or "").strip()
            if not operation_id or operation_id in seen:
                continue
            seen.add(operation_id)

            path = str(action.get("path") or "")
            score_raw = action.get("selectionScore")
            score = float(score_raw) if score_raw is not None else None
            reason = str(action.get("selectionReason") or "").strip()
            if not reason:
                if score is not None:
                    reason = ExternalActionResponseContentService.format(
                        "selectionReasons",
                        "routeSuggestionSemantic",
                        score=f"{score:.2f}",
                    )
                else:
                    reason = ExternalActionResponseContentService.get(
                        "selectionReasons",
                        "routeSuggestionRegistry",
                    )

            out.append(
                {
                    "operationId": operation_id,
                    "actionId": action_id,
                    "domain": ChatOperationalApiDomainService.classify_path(path),
                    "reason": reason,
                    "score": score,
                    "path": path,
                    "method": str(action.get("method") or "GET").upper(),
                    "summary": str(action.get("summary") or action.get("description") or ""),
                }
            )
            if len(out) >= cap:
                break

        return out
