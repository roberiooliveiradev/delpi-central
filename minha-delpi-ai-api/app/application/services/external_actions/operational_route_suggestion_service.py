"""Sugestão dry-run de rotas operacionais (sem execute_external_action)."""

from __future__ import annotations

from app.application.services.external_actions.external_action_candidate_prioritization_service import (
    ExternalActionCandidatePrioritizationService,
)
from app.application.services.external_actions.external_action_selection_support_service import (
    ExternalActionSelectionSupportService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
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
        candidates = self._enrich_candidates_with_domain_paths(
            message,
            candidates,
            allowed_action_ids=allowed,
            provider_key=provider_key,
        )
        # Prioriza domínio (PCP/OTD/…) antes do rank — evita path ASC / embedding
        # devolver comercial quando a frase é claramente produção.
        candidates = ExternalActionCandidatePrioritizationService.apply(message, candidates)
        ranked = self._support.rank_candidates(
            message,
            candidates,
            allowed_action_ids=allowed,
        )
        ranked = self._support.ensure_lexical_ranking(message, ranked)

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
                elif action.get("selectionLexicalMatched"):
                    reason = ExternalActionResponseContentService.get(
                        "selectionReasons",
                        "routeSuggestionLexical",
                    )
                else:
                    reason = ExternalActionResponseContentService.get(
                        "selectionReasons",
                        "routeSuggestionLexical",
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

    def _enrich_candidates_with_domain_paths(
        self,
        message: str,
        candidates: list[dict],
        *,
        allowed_action_ids: list[str],
        provider_key: str,
    ) -> list[dict]:
        """Garante que paths de domínio da frase entrem no pool (evita path ASC truncar)."""
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        markers: list[str] = []

        pcp_triggers = ExternalActionResponseContentService.list(
            "actionSelection",
            "productionPcpOrdersTriggerTerms",
        )
        if any(term in normalized for term in pcp_triggers):
            markers.extend(
                ExternalActionResponseContentService.list(
                    "actionSelection",
                    "routeSuggestionPoolPathMarkers",
                    "pcp",
                )
            )

        production_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "candidatePathPrioritization",
            "productionTerms",
        )
        late_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "productionPcpOrdersLateTerms",
        )
        ops_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "productionPcpOrdersOpsTerms",
        )
        if any(term in normalized for term in production_terms) or (
            any(term in normalized for term in ops_terms)
            and any(term in normalized for term in late_terms)
        ):
            markers.extend(
                ExternalActionResponseContentService.list(
                    "actionSelection",
                    "routeSuggestionPoolPathMarkers",
                    "production",
                )
            )

        if not markers:
            return candidates

        allowed = {str(item) for item in allowed_action_ids}
        by_id = {
            str(action.get("actionId") or ""): action
            for action in candidates
            if action.get("actionId")
        }

        for marker in markers:
            token = str(marker or "").strip()
            if not token:
                continue
            for action in self._support.find_catalog_actions_by_path_token(
                path_token=token,
                provider_key=provider_key,
            ):
                action_id = str(action.get("actionId") or "")
                if not action_id or action_id not in allowed or action_id in by_id:
                    continue
                by_id[action_id] = action

        return list(by_id.values())
