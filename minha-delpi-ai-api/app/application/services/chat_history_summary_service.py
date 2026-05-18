import logging

from app.application.services.chat_intelligence_settings_service import (
    ChatIntelligenceSettingsService,
)
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("minha-delpi-ai-api.chat.history")


class ChatHistorySummaryService:
    def __init__(
        self,
        llm_gateway: LlmGatewayPort,
        intelligence_settings_service: ChatIntelligenceSettingsService | None = None,
    ):
        self.llm_gateway = llm_gateway
        self.intelligence_settings_service = (
            intelligence_settings_service or ChatIntelligenceSettingsService()
        )

    def prepare_history(
        self,
        messages,
        *,
        max_messages: int | None = None,
    ) -> tuple[str, list]:
        keep = max(1, max_messages or Settings.CHAT_HISTORY_MAX_MESSAGES)
        intelligence = self.intelligence_settings_service.resolve()

        if not intelligence.chat_history_summary_enabled:
            return "", list(messages[-keep:])

        if len(messages) <= Settings.CHAT_HISTORY_SUMMARY_TRIGGER_MESSAGES:
            return "", list(messages[-keep:])

        older = list(messages[:-keep])
        recent = list(messages[-keep:])

        if not older:
            return "", recent

        try:
            summary = self._summarize(older)
        except Exception as exc:
            logger.warning("Chat history summary skipped: %s", exc)
            return "", recent

        if not summary:
            return "", recent

        clipped = summary[: Settings.CHAT_HISTORY_SUMMARY_MAX_CHARS]

        return clipped, recent

    def _summarize(self, messages: list) -> str:
        lines: list[str] = []

        for item in messages:
            role = getattr(item, "role", None) or (item.get("role") if isinstance(item, dict) else "unknown")
            content = getattr(item, "content", None) or (
                item.get("content") if isinstance(item, dict) else ""
            )
            normalized = " ".join(str(content or "").split())

            if not normalized:
                continue

            lines.append(f"{role}: {normalized[:500]}")

        if not lines:
            return ""

        conversation = "\n".join(lines[-40:])

        return self.llm_gateway.generate(
            [
                {
                    "role": "system",
                    "content": (
                        "Você resume conversas anteriores de chat corporativo em português do Brasil. "
                        "Preserve fatos, pedidos do usuário, respostas do assistente, números, códigos "
                        "e decisões. Não invente informação. Máximo 8 frases objetivas."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Resuma a conversa anterior:\n\n{conversation}",
                },
            ]
        ).strip()
