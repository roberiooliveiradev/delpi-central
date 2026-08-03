import logging

from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort
from app.domain.services.external_actions.external_action_manifest_text_service import (
    ExternalActionManifestTextService,
)

logger = logging.getLogger("minha-delpi-ai-api.external_actions")


class ExternalActionEmbeddingService:
    def __init__(self, embedding_gateway: EmbeddingGatewayPort):
        self.embedding_gateway = embedding_gateway

    def build_action_text(self, action: dict) -> str:
        return ExternalActionManifestTextService.build(action)

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
