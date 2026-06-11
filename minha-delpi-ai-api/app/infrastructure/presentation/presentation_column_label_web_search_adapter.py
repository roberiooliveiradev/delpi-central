from __future__ import annotations

from app.domain.ports.presentation_column_label_web_search_port import (
    PresentationColumnLabelWebSearchPort,
)
from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService
from app.infrastructure.gateways.web_search_http_gateway import WebSearchHttpGateway


class InfrastructurePresentationColumnLabelWebSearchAdapter(
    PresentationColumnLabelWebSearchPort,
):
    def search(self, query: str, *, max_results: int = 2) -> dict | None:
        if not ChatWebSearchIntentService.is_feature_enabled():
            return None

        gateway = WebSearchHttpGateway()
        payload = gateway.search(query, max_results=max_results)

        return payload if isinstance(payload, dict) else None
