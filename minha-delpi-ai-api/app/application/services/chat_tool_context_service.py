import json

from app.application.dto.execute_tool_request import ExecuteToolRequest
from app.application.use_cases.execute_tool_use_case import ExecuteToolUseCase
from app.domain.services.chat_external_action_direct_answer_service import (
    ChatExternalActionDirectAnswerService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.tool_selection_service import ToolSelectionService
from app.infrastructure.config.settings import Settings
from app.domain.services.external_actions.external_action_result_presenter import ExternalActionResultPresenter


class ChatToolContextService:
    def __init__(
        self,
        tool_selection_service: ToolSelectionService,
        execute_tool_use_case: ExecuteToolUseCase,
        external_action_selection_service=None,
        tool_router_service=None,
        external_action_repository=None,
        native_tool_calling_service=None,
    ):
        self.tool_selection_service = tool_selection_service
        self.execute_tool_use_case = execute_tool_use_case
        self.external_action_selection_service = external_action_selection_service
        self.tool_router_service = tool_router_service
        self.external_action_repository = external_action_repository
        self.native_tool_calling_service = native_tool_calling_service
        self.external_action_result_presenter = ExternalActionResultPresenter()

    def build_context(
        self,
        user_id: str,
        access_token: str,
        message: str,
        allowed_action_ids: list[str] | None = None,
        actions_enabled: bool = True,
        allowed_tool_names: list[str] | None = None,
        fast_path: bool = False,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
    ) -> dict:
        if fast_path:
            return {
                "context": "",
                "toolCalls": [],
                "nativeToolCalling": {"used": False, "providerSupports": False},
            }

        from app.application.services.chat_intelligence_pipeline_service import (
            ChatIntelligencePipelineService,
        )

        raw_message = str(message or "").strip()

        if conversation_context is None and previous_messages:
            conversation_context = ChatIntelligencePipelineService.build_conversation_context(
                previous_messages,
            )

        message = ChatMessageNormalizationService.normalize_for_matching(raw_message) or raw_message

        native_meta = {"used": False, "providerSupports": False}
        native_selections: list[dict] = []

        if self.native_tool_calling_service:
            native_result = self.native_tool_calling_service.select_tools(
                message=message,
                allowed_tool_names=allowed_tool_names,
                tools_registry=self.execute_tool_use_case.tools,
            )
            native_meta = native_result.get("meta") or native_meta
            native_selections = list(native_result.get("selections") or [])

        if native_selections:
            selected_tools = native_selections
        else:
            selected_tools = self.tool_selection_service.select_tools(message)

        if allowed_tool_names:
            allowed = {str(item).strip() for item in allowed_tool_names if str(item).strip()}
            selected_tools = [
                item for item in selected_tools if str(item.get("name") or "") in allowed
            ]

        router_suggestion = {"tools": [], "actionId": None}

        if self.tool_router_service and actions_enabled and not native_selections:
            catalog_actions = []

            if self.external_action_repository and allowed_action_ids:
                catalog_actions = self.external_action_repository.find_candidate_actions(
                    message,
                    limit=Settings.CHAT_TOOL_ROUTER_MAX_ACTIONS,
                    allowed_action_ids=allowed_action_ids,
                )

            router_suggestion = self.tool_router_service.suggest(
                message=message,
                allowed_tool_names=allowed_tool_names,
                allowed_actions=catalog_actions,
            )

            for tool_name in router_suggestion.get("tools") or []:
                if any(str(item.get("name")) == tool_name for item in selected_tools):
                    continue

                selected_tools.append(
                    {
                        "name": tool_name,
                        "arguments": {},
                        "reason": "Ferramenta sugerida pelo roteador inteligente do chat.",
                    }
                )

        selected_external_action = None
        selected_external_action_meta = None

        if self.external_action_selection_service and actions_enabled:
            selected_external_action = self.external_action_selection_service.select_action(
                message,
                allowed_action_ids=allowed_action_ids or [],
                conversation_context=conversation_context,
            )

            if selected_external_action and self._is_external_action_allowed(
                selected_external_action,
                allowed_action_ids,
            ):
                selected_tools.append(selected_external_action)
                arguments = selected_external_action.get("arguments") or {}
                selected_external_action_meta = {
                    "actionId": arguments.get("actionId") or arguments.get("action_id"),
                    "reason": selected_external_action.get("reason"),
                }

        if (
            actions_enabled
            and not selected_external_action
            and router_suggestion.get("actionId")
            and allowed_action_ids
            and str(router_suggestion["actionId"]) in {str(item) for item in allowed_action_ids}
        ):
            selected_tools.append(
                {
                    "name": "execute_external_action",
                    "arguments": {
                        "actionId": router_suggestion["actionId"],
                        "body": {"message": message},
                    },
                    "reason": "Action sugerida pelo roteador inteligente do chat.",
                }
            )

        if not selected_tools:
            return self._finalize_tool_context_result(
                message=raw_message,
                previous_messages=previous_messages,
                result={
                    "context": "",
                    "toolCalls": [],
                    "nativeToolCalling": native_meta,
                    "currentMessage": raw_message,
                },
            )

        context_blocks: list[str] = []
        safe_tool_calls: list[dict] = []
        direct_answer: str | None = None
        skip_rag = False
        last_external_action_data = None

        for selected_tool in selected_tools:
            try:
                result = self.execute_tool_use_case.execute(
                    ExecuteToolRequest(
                        user_id=user_id,
                        access_token=access_token,
                        tool_name=selected_tool["name"],
                        arguments=selected_tool.get("arguments") or {},
                    )
                )
            except Exception as exc:
                tool_name = selected_tool.get("name") or "unknown_tool"
                error_metadata = {
                    "ok": False,
                    "error": str(exc),
                    "errorType": exc.__class__.__name__,
                }

                if tool_name == "execute_external_action":
                    error_metadata["responsePreview"] = self._build_response_preview(
                        error_metadata
                    )

                safe_tool_calls.append(
                    {
                        "name": tool_name,
                        "arguments": selected_tool.get("arguments") or {},
                        "reason": selected_tool.get("reason"),
                        "metadata": error_metadata,
                    }
                )

                context_blocks.append(
                    self._format_tool_error_context(
                        name=tool_name,
                        reason=selected_tool.get("reason"),
                        error=exc,
                    )
                )
                continue

            safe_metadata = self._build_safe_tool_metadata(
                tool_name=result.name,
                metadata=result.metadata,
                data=result.data,
            )
            safe_tool_calls.append(
                {
                    "name": result.name,
                    "arguments": selected_tool.get("arguments") or {},
                    "reason": selected_tool.get("reason"),
                    "metadata": safe_metadata,
                }
            )

            if result.name == "execute_external_action":
                skip_rag = True

                if self._is_successful_external_action(safe_metadata):
                    last_external_action_data = result.data

            # Authorized data is only injected into the LLM context for this request.
            # It is not returned in toolCalls[] and is not persisted in chat metadata.
            context_blocks.append(
                self._format_tool_context(
                    name=result.name,
                    reason=selected_tool.get("reason"),
                    data=result.data,
                    metadata=result.metadata,
                )
            )

        context = "\n\n".join(context_blocks)
        context = context[: Settings.MAX_CONTEXT_CHARS]

        if (
            len(safe_tool_calls) == 1
            and safe_tool_calls[0].get("name") == "execute_external_action"
            and self._is_successful_external_action(safe_tool_calls[0].get("metadata") or {})
        ):
            action_metadata = safe_tool_calls[0].get("metadata") or {}
            direct_answer = self._build_direct_answer(
                last_external_action_data,
                message=message,
                path=action_metadata.get("path"),
                operation_id=action_metadata.get("operationId"),
            )

        requested_format = self._detect_requested_format(message)
        if requested_format:
            self._apply_format_override(safe_tool_calls, requested_format, last_external_action_data)

        return self._finalize_tool_context_result(
            message=raw_message,
            previous_messages=previous_messages,
            result={
                "context": context,
                "toolCalls": safe_tool_calls,
                "nativeToolCalling": native_meta,
                "directAnswer": direct_answer,
                "skipRag": skip_rag,
                "selectedExternalAction": selected_external_action_meta,
                "currentMessage": raw_message,
            },
        )


    def _finalize_tool_context_result(
        self,
        *,
        message: str,
        previous_messages: list | None,
        result: dict,
    ) -> dict:
        from app.application.services.chat_intelligence_pipeline_service import (
            ChatIntelligencePipelineService,
        )

        post_tool = ChatIntelligencePipelineService.finalize_after_tools(
            message,
            previous_messages,
            result,
        )
        finalized = post_tool.tool_context

        if post_tool.analysis_mode:
            finalized["directAnswer"] = None

        return finalized

    _FORMAT_TABLE_HINTS = (
        "em tabela", "formato tabela", "em formato de tabela",
        "mostra em tabela", "mostre em tabela", "como tabela",
        "exibir tabela", "exiba em tabela",
    )
    _FORMAT_CHART_HINTS = (
        "em gráfico", "em grafico", "formato gráfico", "formato grafico",
        "como gráfico", "como grafico", "mostra em gráfico", "mostre em gráfico",
        "em formato de gráfico", "exibir gráfico", "exiba em gráfico",
    )
    _FORMAT_TEXT_HINTS = (
        "em texto", "formato texto", "sem tabela", "sem gráfico",
        "só texto", "so texto", "apenas texto", "formato simples",
        "resumo", "resumido",
    )

    def _detect_requested_format(self, message: str) -> str | None:
        """Detecta se o usuário pediu um formato específico de apresentação."""
        lowered = (message or "").lower()
        if any(h in lowered for h in self._FORMAT_TEXT_HINTS):
            return "text"
        if any(h in lowered for h in self._FORMAT_TABLE_HINTS):
            return "table"
        if any(h in lowered for h in self._FORMAT_CHART_HINTS):
            return "chart"
        return None

    def _apply_format_override(
        self,
        safe_tool_calls: list[dict],
        requested_format: str,
        last_data,
    ) -> None:
        """Sobrescreve a presentation com base no formato solicitado pelo usuário."""
        for tc in safe_tool_calls:
            if tc.get("name") != "execute_external_action":
                continue
            meta = tc.get("metadata")
            if not meta or not meta.get("ok"):
                continue

            if requested_format == "text":
                meta["presentation"] = None
                meta["tablePresentation"] = None

            elif requested_format == "table":
                table_pres = meta.get("tablePresentation") or meta.get("presentation")
                if table_pres and table_pres.get("type") == "table":
                    meta["presentation"] = table_pres
                    meta["tablePresentation"] = None
                elif last_data:
                    path = meta.get("path") or ""
                    forced_table = self.external_action_result_presenter.build_presentation(
                        last_data, path=path
                    )
                    if forced_table:
                        meta["presentation"] = forced_table
                        meta["tablePresentation"] = None

            elif requested_format == "chart":
                chart_pres = meta.get("presentation")
                if chart_pres and chart_pres.get("type") == "chart":
                    pass
                elif last_data:
                    path = meta.get("path") or ""
                    forced_chart = self.external_action_result_presenter.build_chart_presentation(
                        last_data, path=path, force=True
                    )
                    if forced_chart:
                        meta["presentation"] = forced_chart
                        meta["tablePresentation"] = None

    def _build_safe_tool_metadata(
        self,
        tool_name: str,
        metadata: dict | None,
        data,
    ) -> dict:
        safe_metadata = dict(metadata or {})

        if tool_name == "execute_external_action":
            safe_metadata["responsePreview"] = self._build_response_preview(data)

        return safe_metadata

    def _build_response_preview(self, data, max_chars: int = 12000) -> str:
        if data is None:
            return ""

        try:
            text = json.dumps(data, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            text = str(data)

        if len(text) <= max_chars:
            return text

        return f"{text[:max_chars]}\n…"

    def _format_tool_error_context(self, name: str, reason: str | None, error: Exception) -> str:
        payload = {
            "tool": name,
            "reason": reason,
            "ok": False,
            "errorType": error.__class__.__name__,
            "error": str(error),
        }

        return (
            f"[Ferramenta autorizada com erro: {name}]\n"
            "A ferramenta foi selecionada, mas não conseguiu retornar dados.\n"
            "Regra obrigatória: não invente o resultado. Explique o erro em português simples e peça apenas os parâmetros faltantes quando aplicável.\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )

    def _is_external_action_allowed(
        self,
        selected_external_action: dict,
        allowed_action_ids: list[str] | None,
    ) -> bool:
        if not allowed_action_ids:
            return False

        action_id = (
            selected_external_action.get("arguments", {}).get("actionId")
            or selected_external_action.get("arguments", {}).get("action_id")
            or selected_external_action.get("actionId")
            or selected_external_action.get("action_id")
        )

        if not action_id:
            return False

        return str(action_id) in {str(item) for item in allowed_action_ids}

    def _format_tool_context(
        self,
        name: str,
        reason: str | None,
        data,
        metadata: dict | None,
    ) -> str:
        if name == "execute_external_action":
            return self._format_external_action_context(
                reason=reason,
                data=data,
                metadata=metadata or {},
            )

        payload = {
            "tool": name,
            "reason": reason,
            "metadata": metadata or {},
            "authorizedResult": data,
        }

        return (
            f"[Ferramenta autorizada: {name}]\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )

    def _format_external_action_context(
        self,
        reason: str | None,
        data,
        metadata: dict,
    ) -> str:
        status_code = metadata.get("statusCode")
        ok = metadata.get("ok")
        action_id = metadata.get("actionId")
        path = metadata.get("path")
        provider = metadata.get("provider")

        humanized = self.external_action_result_presenter.present(data, path=path or "")

        payload = {
            "tool": "execute_external_action",
            "reason": reason,
            "provider": provider,
            "actionId": action_id,
            "path": path,
            "statusCode": status_code,
            "ok": ok,
            "humanizedSummary": {
                "titulo": humanized.get("titulo"),
                "linhas": humanized.get("linhas"),
            },
        }

        return (
            "[Ferramenta autorizada: execute_external_action]\n"
            "A API externa/interna foi consultada com o token autorizado do usuário.\n"
            f"Provider: {provider}\n"
            f"Action: {action_id}\n"
            f"Path: {path}\n"
            f"Status HTTP: {status_code}\n"
            f"Sucesso: {ok}\n"
            "Regra obrigatória: responda ao usuário em português natural, sem mostrar JSON bruto.\n"
            "Use o resumo humanizado como fonte principal.\n"
            "Se precisar de algum dado técnico, use apenas o resumo técnico compacto.\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )

    def _is_successful_external_action(self, metadata: dict) -> bool:
        if not metadata.get("ok"):
            return False

        status_code = metadata.get("statusCode")

        try:
            return 200 <= int(status_code) < 300
        except (TypeError, ValueError):
            return False

    def _build_direct_answer(
        self,
        data,
        *,
        message: str,
        path: str | None = None,
        operation_id: str | None = None,
    ) -> str | None:
        if not Settings.CHAT_EXTERNAL_ACTION_DIRECT_RESPONSE_ENABLED:
            return None

        humanized = self.external_action_result_presenter.present(data, path=path or "")

        return ChatExternalActionDirectAnswerService.format(
            humanized,
            message=message,
            path=path,
            operation_id=operation_id,
        )

    def _extract_external_action_summary(self, data):
        if not isinstance(data, dict):
            return data

        root = data.get("data", data)

        if isinstance(root, dict) and "data" in root and isinstance(root["data"], dict):
            root = root["data"]

        summary = {}

        product = root.get("product") if isinstance(root, dict) else None
        if isinstance(product, dict):
            summary["product"] = {
                "code": product.get("code"),
                "description": product.get("description"),
                "type": product.get("type"),
                "unit": product.get("unit"),
                "groupCode": product.get("group_code"),
                "active": product.get("active"),
                "defaultWarehouse": product.get("default_warehouse"),
                "lastPurchasePrice": product.get("last_purchase_price"),
                "standardCost": product.get("standard_cost"),
                "lastRevisionDate": product.get("last_revision_date"),
                "ncm": product.get("ncm_ipi_position"),
            }

        stock = root.get("stock") if isinstance(root, dict) else None
        if isinstance(stock, dict):
            summary["stock"] = self._summarize_items(stock.get("items"))

        items = root.get("items") if isinstance(root, dict) else None
        if isinstance(items, list):
            summary["items"] = self._summarize_items(items)

        for key in ["guide", "inspection", "structure", "customers", "suppliers"]:
            value = root.get(key) if isinstance(root, dict) else None
            if isinstance(value, dict):
                summary[key] = {
                    "total": value.get("total"),
                    "items": self._summarize_items(value.get("items")),
                }

        if not summary:
            return root

        return summary

    def _summarize_items(self, items):
        if not isinstance(items, list):
            return []

        return items[:10]
