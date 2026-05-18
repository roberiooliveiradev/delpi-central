import json
import logging
import re

from app.application.services.chat_intelligence_settings_service import (
    ChatIntelligenceSettingsService,
)
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("minha-delpi-ai-api.chat.router")


class ChatToolRouterService:
    def __init__(
        self,
        llm_gateway: LlmGatewayPort,
        intelligence_settings_service: ChatIntelligenceSettingsService | None = None,
    ):
        self.llm_gateway = llm_gateway
        self.intelligence_settings_service = (
            intelligence_settings_service or ChatIntelligenceSettingsService()
        )

    def suggest(
        self,
        *,
        message: str,
        allowed_tool_names: list[str] | None,
        allowed_actions: list[dict],
    ) -> dict:
        intelligence = self.intelligence_settings_service.resolve()

        if not intelligence.chat_tool_router_enabled:
            return {"tools": [], "actionId": None}

        tools = [str(item).strip() for item in (allowed_tool_names or []) if str(item).strip()]
        actions = list(allowed_actions or [])[: Settings.CHAT_TOOL_ROUTER_MAX_ACTIONS]

        if not tools and not actions:
            return {"tools": [], "actionId": None}

        catalog_lines = []

        for name in tools:
            catalog_lines.append(f"- tool:{name}")

        for action in actions:
            catalog_lines.append(
                "- action:{actionId} {method} {path} | {summary}".format(
                    actionId=action.get("actionId"),
                    method=action.get("method"),
                    path=action.get("path"),
                    summary=action.get("summary") or action.get("description") or "",
                )[:220]
            )

        try:
            raw = self.llm_gateway.generate(
                [
                    {
                        "role": "system",
                        "content": (
                            "Você escolhe ferramentas para um assistente corporativo. "
                            "Responda APENAS com JSON válido no formato "
                            '{"tools":["nome_tool"],"actionId":"id_ou_null"}. '
                            "Use somente ids listados. Se nenhuma action for necessária, actionId=null. "
                            "Se nenhuma tool interna for necessária, tools=[]."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Pergunta do usuário:\n{message[:1500]}\n\n"
                            f"Catálogo autorizado:\n" + "\n".join(catalog_lines)
                        ),
                    },
                ]
            )
        except Exception as exc:
            logger.warning("Chat tool router skipped: %s", exc)
            return {"tools": [], "actionId": None}

        return self._parse_response(raw, allowed_tools=tools, allowed_actions=actions)

    def _parse_response(
        self,
        raw: str,
        *,
        allowed_tools: list[str],
        allowed_actions: list[dict],
    ) -> dict:
        payload = self._extract_json(raw)

        if not isinstance(payload, dict):
            return {"tools": [], "actionId": None}

        allowed_tool_set = set(allowed_tools)
        allowed_action_ids = {
            str(action.get("actionId"))
            for action in allowed_actions
            if action.get("actionId")
        }

        tools = [
            str(item).strip()
            for item in (payload.get("tools") or [])
            if str(item).strip() in allowed_tool_set
        ]

        action_id = payload.get("actionId")

        if action_id in (None, "", "null"):
            action_id = None
        elif str(action_id) not in allowed_action_ids:
            action_id = None
        else:
            action_id = str(action_id)

        return {
            "tools": tools,
            "actionId": action_id,
        }

    def _extract_json(self, raw: str) -> dict | list | None:
        text = str(raw or "").strip()

        if not text:
            return None

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", text)

            if not match:
                return None

            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
