import logging

from app.application.services.chat_intelligence_settings_service import (
    ChatIntelligenceSettingsService,
)
from app.application.services.chat_native_tool_schema_service import (
    ChatNativeToolSchemaService,
)
from app.domain.services.chat_tool_context_content_service import (
    ChatToolContextContentService,
)
from app.domain.ports.internal_tool_port import InternalToolPort
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.domain.services.chat_agent_intelligence_policy_service import (
    ChatAgentIntelligencePolicyService,
)

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
        max_tool_calls: int | None = None,
        shortlist_tool_names: list[str] | None = None,
    ) -> dict:
        pilot_enabled = ChatAgentIntelligencePolicyService.native_tool_calling_pilot_enabled(
            agent_context
        )
        provider_supports = self.llm_gateway.supports_native_tools()
        resolved_max = self._resolve_max_tool_calls(
            max_tool_calls,
            agent_context=agent_context,
        )
        shortlist = self._resolve_shortlist(
            allowed_tool_names=allowed_tool_names,
            shortlist_tool_names=shortlist_tool_names,
        )
        meta = {
            "used": False,
            "providerSupports": provider_supports,
            "pilotAgentEnabled": pilot_enabled,
            "shortlistSize": len(shortlist),
            "maxToolCalls": resolved_max,
        }

        if not self.is_enabled(agent_context=agent_context) or not provider_supports:
            return {"selections": [], "meta": meta}

        tv_catalog = None
        if access_token and shortlist and "tv_dashboard_copilot" in set(shortlist):
            try:
                from app.application.services.chat_tv_dashboard_catalog_service import (
                    ChatTvDashboardCatalogService,
                )

                tv_catalog = ChatTvDashboardCatalogService.get_catalog(access_token)
            except Exception:  # noqa: BLE001 — native segue com schema base
                tv_catalog = None

        schemas = self.schema_service.build_openai_tools(
            allowed_tool_names=shortlist,
            tools_registry=tools_registry,
            tv_capability_catalog=tv_catalog if isinstance(tv_catalog, dict) else None,
        )

        meta["schemaCount"] = len(schemas)

        if not schemas:
            return {"selections": [], "meta": meta}

        system_prompt = ChatToolContextContentService.get(
            "nativeToolCalling",
            "systemPrompt",
        )
        selection_reason = ChatToolContextContentService.get(
            "nativeToolCalling",
            "selectionReason",
        )

        try:
            result = self.llm_gateway.generate_with_tools(
                [
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {"role": "user", "content": message[:2000]},
                ],
                schemas,
            )
        except Exception as exc:
            logger.warning("Native tool calling skipped: %s", exc)
            return {"selections": [], "meta": meta}

        shortlist_set = set(shortlist)
        selections = [
            {
                "name": call.name,
                "arguments": call.arguments,
                "reason": selection_reason,
            }
            for call in result.tool_calls
            if call.name in tools_registry and call.name in shortlist_set
        ][:resolved_max]

        meta["used"] = bool(selections)
        meta["toolCount"] = len(selections)
        meta["truncated"] = len(result.tool_calls or []) > len(selections)

        return {"selections": selections, "meta": meta}

    @classmethod
    def _resolve_max_tool_calls(
        cls,
        max_tool_calls: int | None,
        *,
        agent_context: dict | None,
    ) -> int:
        default = ChatToolContextContentService.native_default_max_tool_calls()
        candidates: list[int] = [default]

        if max_tool_calls is not None:
            try:
                candidates.append(max(1, int(max_tool_calls)))
            except (TypeError, ValueError):
                pass

        if isinstance(agent_context, dict):
            raw = agent_context.get("maxToolCalls")
            if raw in (None, ""):
                agent = agent_context.get("agent")
                if isinstance(agent, dict):
                    raw = agent.get("maxToolCalls")
            try:
                if raw not in (None, ""):
                    candidates.append(max(1, int(raw)))
            except (TypeError, ValueError):
                pass

        return max(1, min(candidates))

    @classmethod
    def _resolve_shortlist(
        cls,
        *,
        allowed_tool_names: list[str] | None,
        shortlist_tool_names: list[str] | None,
    ) -> list[str]:
        allowed = [
            str(name).strip()
            for name in (allowed_tool_names or [])
            if str(name).strip()
        ]
        preferred = [
            str(name).strip()
            for name in (shortlist_tool_names or [])
            if str(name).strip()
        ]
        cap = ChatToolContextContentService.native_max_schemas_per_call()

        if preferred:
            allowed_set = set(allowed) if allowed else set(preferred)
            ordered = [name for name in preferred if name in allowed_set]
            if not ordered:
                ordered = preferred
            return ordered[:cap]

        return allowed[:cap]
