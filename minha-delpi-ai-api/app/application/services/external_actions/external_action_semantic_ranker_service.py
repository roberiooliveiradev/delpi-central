import logging

from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort
from app.domain.services.vector_similarity import cosine_similarity
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("minha-delpi-ai-api.external_actions")


class ExternalActionSemanticRankerService:
    def __init__(self, embedding_gateway: EmbeddingGatewayPort):
        self.embedding_gateway = embedding_gateway

    def rank(self, message: str, candidates: list[dict]) -> list[dict]:
        if not Settings.EXTERNAL_ACTION_SEMANTIC_RANK_ENABLED:
            return candidates

        normalized_message = str(message or "").strip()[:2000]

        if not normalized_message or not candidates:
            return candidates

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

        min_score = Settings.EXTERNAL_ACTION_SEMANTIC_MIN_SCORE
        filtered = [action for score, action in scored if score >= min_score]

        for action in filtered:
            action["selectionReason"] = (
                "Action selecionada por similaridade semântica "
                f"(score {action.get('selectionScore')})."
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
