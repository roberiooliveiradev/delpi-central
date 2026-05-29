import json
import logging
import re

from app.application.dto.execute_tool_request import ExecuteToolRequest
from app.application.services.chat_intelligence_settings_service import (
    ChatIntelligenceSettingsService,
)
from app.application.use_cases.execute_tool_use_case import ExecuteToolUseCase
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.domain.services.chat_operational_parameter_service import (
    ChatOperationalParameterService,
)
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("minha-delpi-ai-api.chat.agentic")


class ChatAgenticToolLoopService:
    def __init__(
        self,
        llm_gateway: LlmGatewayPort,
        execute_tool_use_case: ExecuteToolUseCase,
        intelligence_settings_service: ChatIntelligenceSettingsService | None = None,
        external_action_repository=None,
    ):
        self.llm_gateway = llm_gateway
        self.execute_tool_use_case = execute_tool_use_case
        self.intelligence_settings_service = (
            intelligence_settings_service or ChatIntelligenceSettingsService()
        )
        self.external_action_repository = external_action_repository

    def extend_tool_context(
        self,
        *,
        user_id: str,
        access_token: str,
        message: str,
        tool_context: dict,
        allowed_tool_names: list[str] | None,
        allowed_action_ids: list[str] | None,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        on_stream_activity=None,
    ) -> dict:
        settings = self._resolve_settings()

        if not settings["enabled"]:
            return tool_context

        if ChatOperationalParameterService.should_skip_agentic_loop(
            message,
            conversation_context=conversation_context,
            tool_context=tool_context,
            previous_messages=previous_messages,
        ):
            return tool_context

        max_steps = settings["max_steps"]
        catalog = self._build_catalog(
            message,
            allowed_tool_names,
            allowed_action_ids,
        )

        if not catalog:
            return tool_context

        context_blocks: list[str] = []
        safe_tool_calls = list(tool_context.get("toolCalls") or [])
        executed_names = {
            str(item.get("name") or "").strip()
            for item in safe_tool_calls
            if str(item.get("name") or "").strip()
        }
        executed_action_ids = self._collect_executed_action_ids(safe_tool_calls)

        for step in range(max_steps):
            if on_stream_activity:
                from app.application.services.chat_stream_activity_service import (
                    ChatStreamActivityService,
                )

                on_stream_activity(
                    ChatStreamActivityService.plan_step(
                        step=step + 1,
                        total=max_steps,
                        target="ferramentas adicionais",
                        verb="Planejando",
                        state="active",
                        detail="Loop agentic: avaliando se faltam consultas.",
                    )
                )

            plan = self._plan_tools(message, catalog, step=step)

            if not plan.get("tools"):
                if on_stream_activity:
                    from app.application.services.chat_stream_activity_service import (
                        ChatStreamActivityService,
                    )

                    on_stream_activity(
                        ChatStreamActivityService.plan_step(
                            step=step + 1,
                            total=max_steps,
                            target="nenhuma ferramenta extra",
                            verb="Planejado",
                            state="done",
                        )
                    )
                break

            if on_stream_activity:
                from app.application.services.chat_stream_activity_service import (
                    ChatStreamActivityService,
                )

                for tool_index, tool_name in enumerate(plan["tools"], start=1):
                    on_stream_activity(
                        ChatStreamActivityService.plan_step(
                            step=tool_index,
                            total=len(plan["tools"]),
                            target=str(tool_name),
                            verb="Passo",
                            state="done",
                            detail=f"Passo agentic {step + 1}",
                        )
                    )

            for tool_name in plan["tools"]:
                if tool_name in executed_names:
                    continue

                executed_names.add(tool_name)
                tool_arguments = plan.get("arguments", {}).get(tool_name) or {}
                resolved_tool_name = tool_name

                if tool_name.startswith("action:"):
                    action_id = tool_name.split(":", 1)[1].strip()

                    if action_id in executed_action_ids:
                        continue

                    resolved_tool_name = "execute_external_action"
                    tool_arguments = {
                        "actionId": action_id,
                        **tool_arguments,
                    }

                try:
                    result = self.execute_tool_use_case.execute(
                        ExecuteToolRequest(
                            user_id=user_id,
                            access_token=access_token,
                            tool_name=resolved_tool_name,
                            arguments=tool_arguments,
                        )
                    )
                except Exception as exc:
                    safe_tool_calls.append(
                        {
                            "name": resolved_tool_name,
                            "arguments": tool_arguments,
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
                        "arguments": tool_arguments,
                        "reason": "Loop agentic: ferramenta selecionada pelo planejador.",
                        "metadata": {
                            **(result.metadata or {}),
                            "agenticStep": step + 1,
                        },
                    }
                )
                executed_action_ids.update(
                    self._collect_executed_action_ids(safe_tool_calls[-1:])
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

        merged = {
            **tool_context,
            "context": merged_context[: Settings.MAX_CONTEXT_CHARS],
            "toolCalls": safe_tool_calls,
            "agentic": {
                "stepsRun": max_steps,
                "toolsAdded": len(context_blocks),
            },
        }

        return merged

    @staticmethod
    def _collect_executed_action_ids(tool_calls: list[dict]) -> set[str]:
        action_ids: set[str] = set()

        for tool_call in tool_calls:
            arguments = tool_call.get("arguments") or {}
            action_id = str(arguments.get("actionId") or "").strip()

            if action_id:
                action_ids.add(action_id)

            metadata = tool_call.get("metadata") or {}
            meta_action_id = str(metadata.get("actionId") or "").strip()

            if meta_action_id:
                action_ids.add(meta_action_id)

        return action_ids

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
        message: str,
        allowed_tool_names: list[str] | None,
        allowed_action_ids: list[str] | None,
    ) -> list[str]:
        catalog: list[str] = []

        for name in allowed_tool_names or []:
            normalized = str(name).strip()

            if normalized:
                catalog.append(f"tool:{normalized}")

        action_ids = self._resolve_action_ids_for_catalog(message, allowed_action_ids)

        for action_id in action_ids:
            catalog.append(f"action:{action_id}")

        return catalog

    def _resolve_action_ids_for_catalog(
        self,
        message: str,
        allowed_action_ids: list[str] | None,
    ) -> list[str]:
        allowed = [str(item).strip() for item in (allowed_action_ids or []) if str(item).strip()]

        if not allowed:
            return []

        limit = max(1, Settings.CHAT_AGENTIC_CATALOG_MAX_ACTIONS)

        if self.external_action_repository:
            candidates = self.external_action_repository.find_candidate_actions(
                message,
                limit=limit,
                allowed_action_ids=allowed,
            )
            ranked = [
                str(action.get("actionId") or "").strip()
                for action in candidates
                if str(action.get("actionId") or "").strip()
            ]

            if ranked:
                return ranked[:limit]

        return allowed[:limit]

    def _plan_tools(self, message: str, catalog: list[str], *, step: int) -> dict:
        try:
            raw = self.llm_gateway.generate(
                [
                    {
                        "role": "system",
                        "content": (
                            "Planeje ferramentas para responder à pergunta. "
                            'Responda só JSON: {"tools":["nome"],"arguments":{},"done":true|false}. '
                            "Use no máximo UMA action por passo, somente se necessário. "
                            "Use nomes do catálogo: tool:* sem prefixo tool:, ou action:* com prefixo action:."
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

        allowed_tools = {
            item.split(":", 1)[1]
            for item in catalog
            if item.startswith("tool:")
        }
        allowed_actions = {
            item
            for item in catalog
            if item.startswith("action:")
        }

        tools: list[str] = []

        for name in payload.get("tools") or []:
            normalized = str(name).strip()

            if not normalized:
                continue

            if normalized in allowed_tools:
                tools.append(normalized)
            elif normalized in allowed_actions:
                tools.append(normalized)
            elif f"action:{normalized}" in allowed_actions:
                tools.append(f"action:{normalized}")

        if len(tools) > 1:
            tools = tools[:1]

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
