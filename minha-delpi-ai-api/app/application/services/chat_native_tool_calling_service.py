import logging

from app.application.services.chat_intelligence_settings_service import (
    ChatIntelligenceSettingsService,
)
from app.application.services.chat_native_tool_schema_service import (
    ChatNativeToolSchemaService,
)
from app.domain.ports.internal_tool_port import InternalToolPort
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("minha-delpi-ai-api.chat.native_tools")


class ChatNativeToolCallingService:
    def __init__(
        self,
        llm_gateway: LlmGatewayPort,
        schema_service: ChatNativeToolSchemaService | None = None,
        intelligence_settings_service: ChatIntelligenceSettingsService | None = None,
    ):
        self.llm_gateway = llm_gateway
        self.schema_service = schema_service or ChatNativeToolSchemaService()
        self.intelligence_settings_service = (
            intelligence_settings_service or ChatIntelligenceSettingsService()
        )

    def is_enabled(self) -> bool:
        if not Settings.CHAT_NATIVE_TOOL_CALLING_ENABLED:
            return False

        stored = (
            self.intelligence_settings_service.settings_repository.get_chat_intelligence_settings()
            or {}
        )
        enabled = stored.get("nativeToolCallingEnabled")

        if enabled is None:
            return False

        return bool(enabled)

    def select_tools(
        self,
        *,
        message: str,
        allowed_tool_names: list[str] | None,
        tools_registry: dict[str, InternalToolPort],
    ) -> dict:
        meta = {
            "used": False,
            "providerSupports": self.llm_gateway.supports_native_tools(),
        }

        if not self.is_enabled() or not meta["providerSupports"]:
            return {"selections": [], "meta": meta}

        schemas = self.schema_service.build_openai_tools(
            allowed_tool_names=allowed_tool_names,
            tools_registry=tools_registry,
        )

        if not schemas:
            return {"selections": [], "meta": meta}

        try:
            result = self.llm_gateway.generate_with_tools(
                [
                    {
                        "role": "system",
                        "content": (
                            "Selecione ferramentas necessárias para responder à pergunta. "
                            "Use apenas as funções disponíveis. "
                            "Se nenhuma ferramenta for necessária, responda sem chamá-las."
                        ),
                    },
                    {"role": "user", "content": message[:2000]},
                ],
                schemas,
            )
        except Exception as exc:
            logger.warning("Native tool calling skipped: %s", exc)
            return {"selections": [], "meta": meta}

        selections = [
            {
                "name": call.name,
                "arguments": call.arguments,
                "reason": "Ferramenta selecionada via tool-calling nativo do LLM.",
            }
            for call in result.tool_calls
            if call.name in tools_registry
        ]

        meta["used"] = bool(selections)
        meta["toolCount"] = len(selections)

        return {"selections": selections, "meta": meta}
