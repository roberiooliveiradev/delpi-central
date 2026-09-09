"""Retrieval híbrido top-K de actions autorizadas (OpenAPI-first)."""

from __future__ import annotations

from typing import Any, Protocol

from app.application.services.external_actions.external_action_selection_support_service import (
    ExternalActionSelectionSupportService,
)
from app.domain.models.action_descriptor import ActionCandidate, ActionDescriptor
from app.domain.services.openapi_tool_routing_content_service import (
    OpenApiToolRoutingContentService,
)
from app.domain.services.openapi_when_not_to_use_guidance_service import (
    OpenApiWhenNotToUseGuidanceService,
)


class _ActionRepositoryPort(Protocol):
    def list_actions(self, provider_key: str | None = None) -> list[dict]: ...

    def find_candidate_actions(
        self,
        query: str,
        limit: int = 8,
        *,
        allowed_action_ids: list[str] | None = None,
    ) -> list[dict]: ...

    def search_similar_actions(
        self,
        embedding,
        *,
        allowed_action_ids: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict]: ...


class RetrieveActionCandidatesService:
    """Top-K entre allowed_action_ids — sem path markers DELPI nem bias de provider."""

    def __init__(self, repository: _ActionRepositoryPort | None = None, *, semantic_ranker=None):
        self.repository = repository
        self.semantic_ranker = semantic_ranker
        self._support = ExternalActionSelectionSupportService(
            repository,
            semantic_ranker=semantic_ranker,
        )

    def retrieve(
        self,
        message: str,
        *,
        allowed_action_ids: list[str] | None,
        catalog_actions: list[dict[str, Any]] | None = None,
        top_k: int | None = None,
    ) -> list[ActionCandidate]:
        allowed = [
            str(item).strip()
            for item in (allowed_action_ids or [])
            if str(item).strip()
        ]
        if not allowed:
            return []

        pool_limit = OpenApiToolRoutingContentService.int_setting(
            "retrieval",
            "candidatePoolLimit",
            default=120,
        )
        limit = top_k or OpenApiToolRoutingContentService.int_setting(
            "retrieval",
            "topK",
            default=8,
        )
        vector_weight = OpenApiToolRoutingContentService.float_setting(
            "retrieval",
            "vectorWeight",
            default=0.55,
        )
        lexical_weight = OpenApiToolRoutingContentService.float_setting(
            "retrieval",
            "lexicalWeight",
            default=0.45,
        )
        min_score = OpenApiToolRoutingContentService.float_setting(
            "retrieval",
            "minCombinedScore",
            default=0.08,
        )

        actions = self._load_allowed_actions(
            message,
            allowed=allowed,
            catalog_actions=catalog_actions,
            pool_limit=pool_limit,
        )
        if not actions:
            return []

        # Prefer semantic annotation when available, but score the full allowed pool
        # (legacy lexical ranker drops score=0 rows before schema-token boost).
        annotated_by_id: dict[str, dict[str, Any]] = {}
        if self.semantic_ranker:
            ranked_rows = self._support.rank_candidates(
                message,
                actions,
                allowed_action_ids=allowed,
            )
            for row in ranked_rows or []:
                action_id = str(row.get("actionId") or "").strip()
                if action_id:
                    annotated_by_id[action_id] = row

        scored: list[ActionCandidate] = []
        for base in actions:
            row = dict(annotated_by_id.get(str(base.get("actionId") or ""), base))
            lexical = float(
                row.get("selectionLexicalScore")
                if row.get("selectionLexicalScore") is not None
                else ExternalActionSelectionSupportService.lexical_overlap_score(message, row)
            )
            vector = 0.0
            if row.get("selectionVectorScore") is not None:
                vector = float(row.get("selectionVectorScore") or 0.0)
            elif (
                row.get("selectionScore") is not None
                and row.get("selectionLexicalScore") is not None
            ):
                vector = float(row.get("selectionScore") or 0.0)

            boost = self._schema_token_boost(message, row)
            negative = OpenApiWhenNotToUseGuidanceService.penalty(message, row)
            positive = OpenApiWhenNotToUseGuidanceService.bonus(message, row)
            combined = (
                (vector_weight * vector)
                + (lexical_weight * lexical)
                + boost
                + positive
                - negative
            )
            if (
                combined < min_score
                and lexical <= 0
                and vector <= 0
                and boost <= 0
                and negative <= 0
                and positive <= 0
            ):
                continue

            descriptor = ActionDescriptor.from_action_dict(row)
            if not descriptor.action_id or descriptor.action_id not in set(allowed):
                continue

            reasons: list[str] = []
            if lexical > 0:
                reasons.append("lexical")
            if vector > 0:
                reasons.append("vector")
            if boost > 0:
                reasons.append("schema_token")
            if negative > 0:
                reasons.append("when_not_to_use")
            if positive > 0:
                reasons.append("when_to_use")

            scored.append(
                ActionCandidate(
                    descriptor=descriptor,
                    score=combined,
                    lexical_score=lexical,
                    vector_score=vector,
                    reasons=tuple(reasons),
                )
            )

        scored.sort(
            key=lambda item: (
                -item.score,
                0 if item.descriptor.method == "GET" else 1,
                len(item.descriptor.path),
            )
        )
        scored = OpenApiWhenNotToUseGuidanceService.filter_candidates(
            message,
            scored,
            raw_action_of=lambda item: item.raw_action,
        )
        scored = OpenApiWhenNotToUseGuidanceService.prefer_candidates(
            message,
            scored,
            raw_action_of=lambda item: item.raw_action,
        )
        return scored[: max(1, limit)]

    def _load_allowed_actions(
        self,
        message: str,
        *,
        allowed: list[str],
        catalog_actions: list[dict[str, Any]] | None,
        pool_limit: int,
    ) -> list[dict[str, Any]]:
        allowed_set = set(allowed)
        by_id: dict[str, dict[str, Any]] = {}
        catalog = [action for action in (catalog_actions or []) if isinstance(action, dict)]
        repo_actions: list[dict[str, Any]] = []
        if self.repository is not None:
            list_actions = getattr(self.repository, "list_actions", None)
            if callable(list_actions):
                repo_actions = [
                    action for action in list_actions() if isinstance(action, dict)
                ]

        def _put(action: dict[str, Any]) -> None:
            action_id = str(action.get("actionId") or action.get("action_id") or "").strip()
            if action_id and action_id in allowed_set:
                by_id.setdefault(action_id, dict(action))

        for action in catalog + repo_actions:
            if OpenApiWhenNotToUseGuidanceService.matches_positive(message, action):
                _put(action)

        if self.repository is not None:
            find = getattr(self.repository, "find_candidate_actions", None)
            if callable(find):
                for action in find(
                    message,
                    limit=pool_limit,
                    allowed_action_ids=allowed,
                ):
                    if isinstance(action, dict):
                        _put(action)

        for action in catalog:
            if len(by_id) >= pool_limit:
                break
            _put(action)

        for action_id in allowed:
            if len(by_id) >= pool_limit:
                break
            if action_id not in by_id:
                by_id[action_id] = {"actionId": action_id}

        return list(by_id.values())

    @classmethod
    def _schema_token_boost(cls, message: str, action: dict[str, Any]) -> float:
        """Boost genérico por tokens do path/operationId presentes na mensagem (sem markers DELPI)."""
        normalized = str(message or "").lower()
        if not normalized.strip():
            return 0.0
        haystack = " ".join(
            str(action.get(key) or "")
            for key in ("path", "operationId", "summary", "description", "actionId", "tags")
        ).lower()
        if not haystack:
            return 0.0
        boost = 0.0
        # Fragments from operationId / path segments (≥4 chars).
        fragments = set()
        for raw in (
            str(action.get("operationId") or ""),
            str(action.get("path") or "").replace("/", " ").replace("{", " ").replace("}", " "),
            str(action.get("summary") or ""),
        ):
            for part in raw.replace("-", "_").split("_"):
                token = part.strip().lower()
                if len(token) >= 4:
                    fragments.add(token)
        for fragment in fragments:
            if fragment in normalized:
                boost += 0.55
        return boost
