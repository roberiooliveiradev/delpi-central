"""Soft handoff: agente ativo sem action adequada para a intenção operacional.

Não auto-ativa outro agente — só anexa chips / pending para o usuário clicar
(padrão espelhado em ChatCommonChatOperationalGuidanceService).
"""

from __future__ import annotations

from typing import Any

from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.application.services.chat_turn.chat_turn_preparation_content_service import (
    ChatTurnPreparationContentService,
)
from app.application.services.chat_workspace_agent_activation_service import (
    ChatWorkspaceAgentActivationService,
)


class ChatSoftAgentHandoffService:
    ACTION_SWITCH_AND_RESEND = "switch_agent_and_resend"

    @classmethod
    def should_offer(
        cls,
        *,
        message: str | None,
        workspace_context: dict | None,
        tool_calls: list | None,
        tool_context: dict | None = None,
        pipeline_stages: list[str] | None = None,
        intent_route: dict | None = None,
    ) -> bool:
        if not ChatWorkspaceAgentActivationService.operational_tools_enabled(
            workspace_context
        ):
            return False

        query = str(message or "").strip()
        if not query:
            return False

        if not cls._is_operational_intent(
            message=query,
            intent_route=intent_route,
        ):
            return False

        if cls._has_selected_external_action(
            tool_calls=tool_calls,
            tool_context=tool_context,
        ):
            return False

        stages = [str(item) for item in (pipeline_stages or [])]
        tools_ran = "tools" in stages
        calls = [
            item
            for item in (tool_calls or [])
            if isinstance(item, dict)
        ]
        empty_calls = len(calls) == 0

        if tools_ran and empty_calls and cls._requires_tool(intent_route):
            return True

        if empty_calls and ChatCapabilitiesService.looks_like_operational_data_request(
            query
        ):
            # Miss de seleção (selectedExternalAction null) com pedido operacional.
            return tools_ran or cls._requires_tool(intent_route)

        return False

    @classmethod
    def build_follow_up_suggestions(cls, message: str | None) -> list[dict[str, Any]]:
        query = str(message or "").strip()
        if not query:
            return []

        label = ChatTurnPreparationContentService.get(
            "directAnswers",
            "softAgentHandoff",
            "switchAndResendLabel",
        ) or "Trocar para Agente Minha DELPI e repetir esta consulta"

        return [
            {
                "label": label,
                "query": query,
                "group": "ajuda",
                "priority": 1,
                "action": cls.ACTION_SWITCH_AND_RESEND,
            }
        ]

    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        message: str | None,
        workspace_context: dict | None,
        tool_calls: list | None,
        tool_context: dict | None = None,
        pipeline_stages: list[str] | None = None,
        intent_route: dict | None = None,
    ) -> None:
        if not cls.should_offer(
            message=message,
            workspace_context=workspace_context,
            tool_calls=tool_calls,
            tool_context=tool_context,
            pipeline_stages=pipeline_stages,
            intent_route=intent_route,
        ):
            return

        query = str(message or "").strip()
        if not query:
            return

        metadata["pendingOperationalQuery"] = query
        metadata["softAgentHandoff"] = True

        suggestions = cls.build_follow_up_suggestions(query)
        if not suggestions:
            return

        existing = metadata.get("followUpSuggestions")
        if isinstance(existing, list) and existing:
            handoff_labels = {
                str(item.get("label") or "") for item in suggestions if isinstance(item, dict)
            }
            merged = list(suggestions)
            for item in existing:
                if not isinstance(item, dict):
                    continue
                if str(item.get("label") or "") in handoff_labels:
                    continue
                merged.append(item)
            metadata["followUpSuggestions"] = merged
        else:
            metadata["followUpSuggestions"] = suggestions

    @classmethod
    def _is_operational_intent(
        cls,
        *,
        message: str,
        intent_route: dict | None,
    ) -> bool:
        route = intent_route if isinstance(intent_route, dict) else {}
        intent = str(route.get("intent") or "").strip()

        if intent == "operational_query":
            return True

        if cls._requires_tool(route):
            return True

        return ChatCapabilitiesService.looks_like_operational_data_request(message)

    @staticmethod
    def _requires_tool(intent_route: dict | None) -> bool:
        route = intent_route if isinstance(intent_route, dict) else {}
        if route.get("requiresTool") is True:
            return True
        return str(route.get("intent") or "").strip() == "operational_query"

    @classmethod
    def _has_selected_external_action(
        cls,
        *,
        tool_calls: list | None,
        tool_context: dict | None,
    ) -> bool:
        ctx = tool_context if isinstance(tool_context, dict) else {}
        selected = ctx.get("selectedExternalAction")
        if isinstance(selected, dict) and (
            selected.get("actionId") or selected.get("path") or selected.get("operationId")
        ):
            return True

        for call in tool_calls or []:
            if not isinstance(call, dict):
                continue
            name = str(call.get("name") or call.get("tool") or "").strip()
            if name in {"execute_external_action", "external_action"}:
                return True
            meta = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}
            if meta.get("actionId") or meta.get("path"):
                return True

        return False
