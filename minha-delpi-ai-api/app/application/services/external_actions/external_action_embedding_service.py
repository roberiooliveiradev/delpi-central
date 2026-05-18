import logging

from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort

logger = logging.getLogger("minha-delpi-ai-api.external_actions")


class ExternalActionEmbeddingService:
    def __init__(self, embedding_gateway: EmbeddingGatewayPort):
        self.embedding_gateway = embedding_gateway

    def build_action_text(self, action: dict) -> str:
        tags = action.get("tags") or []
        tag_text = ", ".join(str(item) for item in tags) if isinstance(tags, list) else str(tags)

        return " | ".join(
            part
            for part in [
                str(action.get("method") or "").upper(),
                str(action.get("path") or ""),
                str(action.get("summary") or ""),
                str(action.get("description") or ""),
                str(action.get("operationId") or action.get("operation_id") or ""),
                tag_text,
            ]
            if part
        )[:4000]

    def embed_action(self, action: dict) -> list[float] | None:
        text = self.build_action_text(action).strip()

        if not text:
            return None

        try:
            return self.embedding_gateway.embed(text)
        except Exception as exc:
            logger.warning(
                "Failed to embed action %s: %s",
                action.get("actionId") or action.get("action_id"),
                exc,
            )
            return None
