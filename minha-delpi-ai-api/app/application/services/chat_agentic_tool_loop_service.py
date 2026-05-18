import json
import logging
import re

from app.application.dto.execute_tool_request import ExecuteToolRequest
from app.application.services.chat_intelligence_settings_service import (
    ChatIntelligenceSettingsService,
)
from app.application.use_cases.execute_tool_use_case import ExecuteToolUseCase
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("minha-delpi-ai-api.chat.agentic")


class ChatAgenticToolLoopService:
    def __init__(
        self,
        llm_gateway: LlmGatewayPort,
        execute_tool_use_case: ExecuteToolUseCase,
        intelligence_settings_service: ChatIntelligenceSettingsService | None = None,
    ):
        self.llm_gateway = llm_gateway
        self.execute_tool_use_case = execute_tool_use_case
        self.intelligence_settings_service = (
            intelligence_settings_service or ChatIntelligenceSettingsService()
        )

    def extend_tool_context(
        self,
        *,
        user_id: str,
        access_token: str,
        message: str,
        tool_context: dict,
        allowed_tool_names: list[str] | None,
        allowed_action_ids: list[str] | None,
    ) -> dict:
        settings = self._resolve_settings()

        if not settings["enabled"]:
            return tool_context

        max_steps = settings["max_steps"]
        catalog = self._build_catalog(allowed_tool_names, allowed_action_ids)

        if not catalog:
            return tool_context

        context_blocks: list[str] = []
        safe_tool_calls = list(tool_context.get("toolCalls") or [])
        executed_names = {
            str(item.get("name") or "").strip()
            for item in safe_tool_calls
            if str(item.get("name") or "").strip()
        }

        for step in range(max_steps):
            plan = self._plan_tools(message, catalog, step=step)

            if not plan.get("tools"):
                break

            for tool_name in plan["tools"]:
                if tool_name in executed_names:
                    continue

                executed_names.add(tool_name)

                try:
                    result = self.execute_tool_use_case.execute(
                        ExecuteToolRequest(
                            user_id=user_id,
                            access_token=access_token,
                            tool_name=tool_name,
                            arguments=plan.get("arguments", {}).get(tool_name) or {},
                        )
                    )
                except Exception as exc:
                    safe_tool_calls.append(
                        {
                            "name": tool_name,
                            "arguments": plan.get("arguments", {}).get(tool_name) or {},
                            "reason": "Loop agentic: execução da ferramenta.",
                            "metadata": {
                                "ok": False,
                                "error": str(exc),
                                "agenticStep": step + 1,
                            },
                        }
                    )
                    continue

                safe_tool_calls.append(
                    {
                        "name": result.name,
                        "arguments": plan.get("arguments", {}).get(tool_name) or {},
                        "reason": "Loop agentic: ferramenta selecionada pelo planejador.",
                        "metadata": {
                            **(result.metadata or {}),
                            "agenticStep": step + 1,
                        },
                    }
                )

                context_blocks.append(
                    json.dumps(
                        {
                            "tool": result.name,
                            "agenticStep": step + 1,
                            "authorizedResult": result.data,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )

            if plan.get("done"):
                break

        if not context_blocks:
            return tool_context

        existing_context = str(tool_context.get("context") or "").strip()
        parts = [existing_context, *context_blocks] if existing_context else context_blocks
        merged_context = "\n\n".join(part for part in parts if part).strip()

        return {
            "context": merged_context[: Settings.MAX_CONTEXT_CHARS],
            "toolCalls": safe_tool_calls,
            "agentic": {
                "stepsRun": max_steps,
                "toolsAdded": len(context_blocks),
            },
        }

    def _resolve_settings(self) -> dict:
        runtime = self.intelligence_settings_service.resolve()
        stored = self.intelligence_settings_service.settings_repository.get_chat_intelligence_settings() or {}

        enabled = stored.get("agenticLoopEnabled")
        if enabled is None:
            enabled = Settings.CHAT_AGENTIC_LOOP_ENABLED

        max_steps = stored.get("agenticLoopMaxSteps")
        if max_steps is None:
            max_steps = Settings.CHAT_AGENTIC_LOOP_MAX_STEPS

        return {
            "enabled": bool(enabled),
            "max_steps": max(1, min(int(max_steps), 3)),
        }

    def _build_catalog(
        self,
        allowed_tool_names: list[str] | None,
        allowed_action_ids: list[str] | None,
    ) -> list[str]:
        catalog: list[str] = []

        for name in allowed_tool_names or []:
            normalized = str(name).strip()

            if normalized:
                catalog.append(f"tool:{normalized}")

        for action_id in (allowed_action_ids or [])[:10]:
            catalog.append(f"action:{action_id}")

        return catalog

    def _plan_tools(self, message: str, catalog: list[str], *, step: int) -> dict:
        try:
            raw = self.llm_gateway.generate(
                [
                    {
                        "role": "system",
                        "content": (
                            "Planeje ferramentas para responder a pergunta. "
                            'Responda só JSON: {"tools":["nome"],"arguments":{},"done":true|false}. '
                            "Use apenas nomes do catálogo sem prefixo tool:."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Passo {step + 1}\nPergunta: {message[:1200]}\n"
                            f"Catálogo:\n" + "\n".join(catalog)
                        ),
                    },
                ]
            )
        except Exception as exc:
            logger.warning("Agentic planner skipped: %s", exc)
            return {"tools": [], "done": True}

        payload = self._extract_json(raw)

        if not isinstance(payload, dict):
            return {"tools": [], "done": True}

        allowed = {
            item.split(":", 1)[1]
            for item in catalog
            if item.startswith("tool:")
        }

        tools = [
            str(name).strip()
            for name in (payload.get("tools") or [])
            if str(name).strip() in allowed
        ]

        return {
            "tools": tools,
            "arguments": payload.get("arguments") if isinstance(payload.get("arguments"), dict) else {},
            "done": bool(payload.get("done", True)),
        }

    def _extract_json(self, raw: str) -> dict | list | None:
        text = str(raw or "").strip()

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
