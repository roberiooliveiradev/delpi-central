import json

from app.application.dto.execute_tool_request import ExecuteToolRequest
from app.application.use_cases.execute_tool_use_case import ExecuteToolUseCase
from app.domain.services.tool_selection_service import ToolSelectionService
from app.infrastructure.config.settings import Settings
from app.domain.services.external_actions.external_action_result_presenter import ExternalActionResultPresenter


class ChatToolContextService:
    def __init__(
        self,
        tool_selection_service: ToolSelectionService,
        execute_tool_use_case: ExecuteToolUseCase,
        external_action_selection_service=None,
    ):
        self.tool_selection_service = tool_selection_service
        self.execute_tool_use_case = execute_tool_use_case
        self.external_action_selection_service = external_action_selection_service
        self.external_action_result_presenter = ExternalActionResultPresenter()

    def build_context(
        self,
        user_id: str,
        access_token: str,
        message: str,
        allowed_action_ids: list[str] | None = None,
        actions_enabled: bool = True,
        allowed_tool_names: list[str] | None = None,
    ) -> dict:
        selected_tools = self.tool_selection_service.select_tools(message)

        if allowed_tool_names:
            allowed = {str(item).strip() for item in allowed_tool_names if str(item).strip()}
            selected_tools = [
                item for item in selected_tools if str(item.get("name") or "") in allowed
            ]

        if self.external_action_selection_service and actions_enabled:
            selected_external_action = self.external_action_selection_service.select_action(
                message,
                allowed_action_ids=allowed_action_ids or [],
            )

            if selected_external_action and self._is_external_action_allowed(
                selected_external_action,
                allowed_action_ids,
            ):
                selected_tools.append(selected_external_action)

        if not selected_tools:
            return {
                "context": "",
                "toolCalls": [],
            }

        context_blocks: list[str] = []
        safe_tool_calls: list[dict] = []

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

            # Safe metadata returned to the client and persisted in chat metadata.
            # Do not include raw tool data here. Raw data may contain user profile,
            # e-mail, permissions or operational values.
            safe_tool_calls.append(
                {
                    "name": result.name,
                    "arguments": selected_tool.get("arguments") or {},
                    "reason": selected_tool.get("reason"),
                    "metadata": result.metadata,
                }
            )

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

        return {
            "context": context,
            "toolCalls": safe_tool_calls,
        }


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

        extracted = self._extract_external_action_summary(data)
        humanized = self.external_action_result_presenter.present(data)

        payload = {
            "tool": "execute_external_action",
            "reason": reason,
            "provider": provider,
            "actionId": action_id,
            "path": path,
            "statusCode": status_code,
            "ok": ok,
            "humanizedSummary": humanized,
            "technicalSummary": extracted,
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
