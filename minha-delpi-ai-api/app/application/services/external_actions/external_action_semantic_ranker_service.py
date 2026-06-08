import logging

from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)
from app.domain.services.vector_similarity import cosine_similarity
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("minha-delpi-ai-api.external_actions")


class ExternalActionSemanticRankerService:
    def __init__(
        self,
        embedding_gateway: EmbeddingGatewayPort,
        external_action_repository=None,
        intelligence_settings_service=None,
    ):
        self.embedding_gateway = embedding_gateway
        self.external_action_repository = external_action_repository
        if intelligence_settings_service is None:
            from app.application.services.chat_intelligence_settings_service import (
                ChatIntelligenceSettingsService,
            )

            intelligence_settings_service = ChatIntelligenceSettingsService()

        self.intelligence_settings_service = intelligence_settings_service

    def rank(
        self,
        message: str,
        candidates: list[dict],
        *,
        allowed_action_ids: list[str] | None = None,
    ) -> list[dict]:
        intelligence = self.intelligence_settings_service.resolve()

        if not intelligence.external_action_semantic_rank_enabled:
            return candidates

        normalized_message = str(message or "").strip()[:2000]

        if not normalized_message or not candidates:
            return candidates

        min_score = intelligence.external_action_semantic_min_score
        allowed_ids = allowed_action_ids or [
            str(item.get("actionId"))
            for item in candidates
            if item.get("actionId")
        ]

        if self.external_action_repository:
            try:
                message_embedding = self.embedding_gateway.embed(normalized_message)
                similar = self.external_action_repository.search_similar_actions(
                    message_embedding,
                    allowed_action_ids=allowed_ids,
                    limit=Settings.EXTERNAL_ACTION_SEMANTIC_RANK_LIMIT,
                )

                if similar:
                    return self._finalize_ranked(similar, min_score=min_score)
            except Exception as exc:
                logger.warning("Vector action search skipped: %s", exc)

        limited = candidates[: Settings.EXTERNAL_ACTION_SEMANTIC_RANK_LIMIT]

        try:
            message_embedding = self.embedding_gateway.embed(normalized_message)
        except Exception as exc:
            logger.warning("External action semantic rank skipped: %s", exc)
            return candidates

        scored: list[tuple[float, dict]] = []

        for action in limited:
            action_text = self._action_text(action)

            try:
                action_embedding = self.embedding_gateway.embed(action_text)
                score = cosine_similarity(message_embedding, action_embedding)
            except Exception:
                score = 0.0

            enriched = dict(action)
            enriched["selectionScore"] = round(score, 4)
            scored.append((score, enriched))

        scored.sort(
            key=lambda item: (
                -item[0],
                0 if str(item[1].get("method") or "").upper() == "GET" else 1,
                len(str(item[1].get("path") or "")),
            )
        )

        filtered = [action for score, action in scored if score >= min_score]

        return self._finalize_ranked(filtered, min_score=min_score)

    def _finalize_ranked(self, actions: list[dict], *, min_score: float) -> list[dict]:
        filtered = [
            action
            for action in actions
            if action.get("selectionScore") is None
            or float(action["selectionScore"]) >= min_score
        ]

        for action in filtered:
            action["selectionReason"] = ExternalActionResponseContentService.format(
                "selectionReasons",
                "semanticRankReason",
                score=action.get("selectionScore"),
            )

        return filtered

    def _action_text(self, action: dict) -> str:
        tags = action.get("tags") or []
        tag_text = ", ".join(str(item) for item in tags) if isinstance(tags, list) else str(tags)

        return " | ".join(
            part
            for part in [
                str(action.get("method") or "").upper(),
                str(action.get("path") or ""),
                str(action.get("summary") or ""),
                str(action.get("description") or ""),
                str(action.get("operationId") or ""),
                tag_text,
            ]
            if part
        )[:4000]
