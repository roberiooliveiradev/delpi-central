import logging

from app.application.services.chat_intelligence_settings_service import (
    ChatIntelligenceSettingsService,
)
from app.domain.services.chat_agent_intelligence_policy_service import (
    ChatAgentIntelligencePolicyService,
)
from app.application.services.chat_native_tool_schema_service import (
    ChatNativeToolSchemaService,
)
from app.domain.ports.internal_tool_port import InternalToolPort
from app.domain.ports.llm_gateway_port import LlmGatewayPort

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

    def is_enabled(self, *, agent_context: dict | None = None) -> bool:
        if not self.intelligence_settings_service.resolve().native_tool_calling_enabled:
            return False

        return ChatAgentIntelligencePolicyService.native_tool_calling_pilot_enabled(
            agent_context
        )

    def select_tools(
        self,
        *,
        message: str,
        allowed_tool_names: list[str] | None,
        tools_registry: dict[str, InternalToolPort],
        agent_context: dict | None = None,
        access_token: str | None = None,
    ) -> dict:
        pilot_enabled = ChatAgentIntelligencePolicyService.native_tool_calling_pilot_enabled(
            agent_context
        )
        meta = {
            "used": False,
            "providerSupports": self.llm_gateway.supports_native_tools(),
            "pilotAgentEnabled": pilot_enabled,
        }

        if not self.is_enabled(agent_context=agent_context) or not meta["providerSupports"]:
            return {"selections": [], "meta": meta}

        tv_catalog = None
        if access_token and allowed_tool_names and "tv_dashboard_copilot" in {
            str(n).strip() for n in allowed_tool_names
        }:
            try:
                from app.application.services.chat_tv_dashboard_catalog_service import (
                    ChatTvDashboardCatalogService,
                )

                tv_catalog = ChatTvDashboardCatalogService.get_catalog(access_token)
            except Exception:  # noqa: BLE001 — native segue com schema base
                tv_catalog = None

        schemas = self.schema_service.build_openai_tools(
            allowed_tool_names=allowed_tool_names,
            tools_registry=tools_registry,
            tv_capability_catalog=tv_catalog if isinstance(tv_catalog, dict) else None,
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
