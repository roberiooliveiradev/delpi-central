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
        catalog_keys, catalog_schemas = self._build_catalog(
            message,
            allowed_tool_names,
            allowed_action_ids,
        )

        if not catalog_keys:
            return tool_context

        catalog_action_ids = [
            item.split(":", 1)[1]
            for item in catalog_keys
            if item.startswith("action:")
        ]

        context_blocks: list[str] = []
        # Falhas acumuladas alimentam o replanejamento: o planejador tenta uma
        # alternativa (outra rota/abordagem) em vez de repetir o que já falhou.
        failures: list[str] = []
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

            plan = self._plan_tools(
                message,
                catalog_keys,
                catalog_schemas,
                step=step,
                failures=failures,
            )

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

            agentic_total = len(plan["tools"])

            for tool_position, tool_name in enumerate(plan["tools"], start=1):
                if tool_name in executed_names:
                    continue

                executed_names.add(tool_name)
                tool_arguments = plan.get("arguments", {}).get(tool_name) or {}
                resolved_tool_name = tool_name
                resolved_action_id = ""

                if tool_name.startswith("action:"):
                    action_id = tool_name.split(":", 1)[1].strip()
                    resolved_action_id = action_id

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
                    failure_metadata = {
                        "ok": False,
                        "error": str(exc),
                        "agenticStep": step + 1,
                    }
                    safe_tool_calls.append(
                        {
                            "name": resolved_tool_name,
                            "arguments": tool_arguments,
                            "reason": "Loop agentic: execução da ferramenta.",
                            "metadata": failure_metadata,
                        }
                    )
                    # Avisa o usuário no log que esta etapa falhou (não fica silencioso).
                    self._emit_tool_finished(
                        on_stream_activity,
                        index=tool_position,
                        total=agentic_total,
                        metadata=failure_metadata,
                        action_id=resolved_action_id or None,
                    )
                    # Registra para o próximo passo tentar contornar com outra abordagem.
                    failures.append(
                        self._summarize_failure(
                            failure_metadata,
                            resolved_action_id or resolved_tool_name,
                        )
                    )
                    continue

                result_metadata = {
                    **(result.metadata or {}),
                    "agenticStep": step + 1,
                }
                safe_tool_calls.append(
                    {
                        "name": result.name,
                        "arguments": tool_arguments,
                        "reason": "Loop agentic: ferramenta selecionada pelo planejador.",
                        "metadata": result_metadata,
                    }
                )
                self._emit_tool_finished(
                    on_stream_activity,
                    index=tool_position,
                    total=agentic_total,
                    metadata=result_metadata,
                    action_id=resolved_action_id or None,
                    data=result.data,
                )
                executed_action_ids.update(
                    self._collect_executed_action_ids(safe_tool_calls[-1:])
                )

                # Falha que NÃO levantou exceção (ex.: HTTP 4xx/5xx): registra para
                # o planejador contornar no próximo passo e não usa o payload de erro
                # como "resultado autorizado" para o LLM.
                if self._looks_like_failure(result_metadata):
                    failures.append(
                        self._summarize_failure(
                            result_metadata,
                            resolved_action_id or result.name,
                        )
                    )
                    continue

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
            base = {**tool_context}
            # Mesmo sem contexto novo, propaga as chamadas que falharam para a
            # camada de tratamento de erros (§27) enriquecer a resposta com
            # motivos + chips de recuperação, em vez do erro passar despercebido.
            if failures:
                base["toolCalls"] = safe_tool_calls

            if catalog_action_ids:
                base["agentic"] = {
                    "stepsRun": max_steps,
                    "toolsAdded": 0,
                    "catalogSize": len(catalog_action_ids),
                    "catalogMaxActions": Settings.CHAT_AGENTIC_CATALOG_MAX_ACTIONS,
                }

            return base

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
                "catalogSize": len(catalog_action_ids),
                "catalogMaxActions": Settings.CHAT_AGENTIC_CATALOG_MAX_ACTIONS,
            },
        }

        return merged

    @staticmethod
    def _looks_like_failure(metadata: dict) -> bool:
        """Falha explícita (ok=False) ou status HTTP fora da faixa 2xx."""
        if not isinstance(metadata, dict):
            return False

        if "ok" in metadata and not metadata.get("ok"):
            return True

        status = metadata.get("statusCode")

        if status is not None:
            try:
                return not (200 <= int(status) < 300)
            except (TypeError, ValueError):
                return False

        return False

    @staticmethod
    def _summarize_failure(metadata: dict, label: str) -> str:
        meta = metadata if isinstance(metadata, dict) else {}
        status = meta.get("statusCode")
        reason = str(meta.get("error") or meta.get("message") or "").strip()
        clean_label = str(label or "consulta").strip() or "consulta"
        suffix = f" (HTTP {status})" if status not in (None, "") else ""

        if reason:
            return f"{clean_label}{suffix}: {reason[:160]}"

        return f"{clean_label}{suffix}: falha na consulta"

    @staticmethod
    def _emit_tool_finished(
        on_stream_activity,
        *,
        index: int,
        total: int,
        metadata: dict,
        action_id: str | None = None,
        data: object | None = None,
    ) -> None:
        """Emite a etapa de conclusão da ferramenta no log (sucesso, vazio ou falha)."""
        if not on_stream_activity:
            return

        from app.application.services.chat_stream_activity_service import (
            ChatStreamActivityService,
        )

        on_stream_activity(
            ChatStreamActivityService.tool_finished(
                index=index,
                total=total,
                metadata=metadata if isinstance(metadata, dict) else {},
                action_id=action_id,
                data=data,
            )
        )

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
    ) -> tuple[list[str], list[dict]]:
        from app.domain.services.chat_agentic_catalog_service import (
            ChatAgenticCatalogService,
        )

        catalog_keys: list[str] = []

        for name in allowed_tool_names or []:
            normalized = str(name).strip()

            if normalized:
                catalog_keys.append(f"tool:{normalized}")

        slim_actions = ChatAgenticCatalogService.build_slim_catalog(
            message,
            allowed_action_ids,
            self.external_action_repository,
        )

        for action in slim_actions:
            action_id = str(action.get("actionId") or "").strip()

            if action_id:
                catalog_keys.append(f"action:{action_id}")

        return catalog_keys, slim_actions

    def _plan_tools(
        self,
        message: str,
        catalog: list[str],
        catalog_schemas: list[dict],
        *,
        step: int,
        failures: list[str] | None = None,
    ) -> dict:
        from app.domain.services.chat_agentic_action_schema_service import (
            ChatAgenticActionSchemaService,
        )

        planner_catalog = ChatAgenticActionSchemaService.format_planner_catalog(
            catalog_schemas,
        )
        tool_lines = [
            item
            for item in catalog
            if item.startswith("tool:")
        ]

        system_content = (
            "Planeje ferramentas para responder à pergunta. "
            'Responda só JSON: {"tools":["nome"],"arguments":{},"done":true|false}. '
            "Use no máximo UMA action por passo, somente se necessário. "
            "Use nomes do catálogo: tool:* sem prefixo tool:, ou action:* com prefixo action:. "
            "Quando escolher action:*, preencha arguments conforme exampleArguments do catálogo."
        )

        failure_block = ""

        if failures:
            recent = failures[-5:]
            system_content += (
                " Algumas consultas anteriores falharam. NÃO repita a mesma consulta "
                "que falhou: tente uma ABORDAGEM ALTERNATIVA (outra action, outros "
                "parâmetros, busca por descrição em vez de código, ou ampliar filtros). "
                'Se não houver alternativa viável, responda {"tools":[],"done":true}.'
            )
            failure_block = "\nConsultas que já falharam (evite repetir):\n" + "\n".join(
                f"- {item}" for item in recent
            )

        try:
            raw = self.llm_gateway.generate(
                [
                    {
                        "role": "system",
                        "content": system_content,
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Passo {step + 1}\nPergunta: {message[:1200]}\n"
                            f"Tools internas:\n" + "\n".join(tool_lines or ["(nenhuma)"]) + "\n"
                            f"Actions OpenAPI (descrição + parâmetros + exemplos):\n{planner_catalog}"
                            f"{failure_block}"
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
