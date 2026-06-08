"""Drawing, direct answer e SQL recovery do turno de tools — Fase 3C lote 11."""

from __future__ import annotations

from app.application.services.chat_tool_context_content_service import (
    ChatToolContextContentService,
)
from app.application.services.chat_tool_context_external_action_formatter import (
    ChatToolContextExternalActionFormatter,
)
from app.domain.services.chat_external_action_direct_answer_service import (
    ChatExternalActionDirectAnswerService,
)
from app.domain.services.chat_tool_context_presentation_service import (
    ChatToolContextPresentationService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from app.infrastructure.config.settings import Settings


class ChatToolContextAuxiliaryService:
    def __init__(
        self,
        presenter: ExternalActionResultPresenter,
        formatter: ChatToolContextExternalActionFormatter,
        *,
        execute_tool_use_case=None,
        external_action_repository=None,
    ) -> None:
        self._presenter = presenter
        self._formatter = formatter
        self._execute_tool_use_case = execute_tool_use_case
        self._external_action_repository = external_action_repository

    def _build_drawing_pdf_extract_summary(
            self,
            pdf_extract: dict | None,
            *,
            product_code_source: str | None = None,
        ) -> dict:
            if not isinstance(pdf_extract, dict):
                return {}

            component_codes = pdf_extract.get("componentCodes")
            if not isinstance(component_codes, list):
                component_codes = []

            summary = {
                "productCode": pdf_extract.get("productCode"),
                "revision": pdf_extract.get("revision"),
                "legible": pdf_extract.get("legible"),
                "charCount": pdf_extract.get("charCount"),
                "componentCount": len(component_codes),
                "reason": pdf_extract.get("reason"),
                "extractor": pdf_extract.get("extractor"),
                "documentVision": pdf_extract.get("documentVision"),
            }

            if product_code_source:
                summary["productCodeSource"] = product_code_source

            return summary

    def _build_drawing_analysis_enrichment(
            self,
            *,
            safe_tool_calls: list[dict],
            product_code: str | None,
            has_pdf_attachment: bool,
            direct_answer: str | None,
            pdf_extract: dict | None = None,
        ) -> dict | None:
            from app.domain.services.chat_drawing_validation_orchestration_service import (
                ChatDrawingValidationOrchestrationService,
            )

            code = str(product_code or "").strip()

            for tool_call in ChatToolContextPresentationService._successful_external_action_tool_calls(safe_tool_calls):
                metadata = tool_call.get("metadata") or {}
                path = str(metadata.get("path") or "")

                if "/analyser" not in path.lower():
                    continue

                if not code:
                    arguments = tool_call.get("arguments") or {}
                    code = str(arguments.get("code") or arguments.get("productCode") or "").strip()

                data = tool_call.get("data")

                if data is None:
                    data = metadata.get("authorizedResult") or metadata.get("data")

                root = data.get("data", data) if isinstance(data, dict) else {}

                if isinstance(root, dict) and isinstance(root.get("data"), dict):
                    root = root["data"]

                package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
                    product_code=code or "—",
                    payload=root if isinstance(root, dict) else None,
                    has_pdf_attachment=has_pdf_attachment,
                    api_ok=bool(metadata.get("ok")),
                    api_status_code=metadata.get("statusCode"),
                    pdf_extract=pdf_extract,
                )

                report_markdown = ChatDrawingValidationOrchestrationService.format_report_markdown(
                    package
                )

                from app.application.services.chat_drawing_report_export_service import (
                    ChatDrawingReportExportService,
                )

                export_payload = ChatDrawingReportExportService.build_export_payload(
                    package=package,
                    report_markdown=report_markdown,
                )

                return {
                    "directAnswer": ChatDrawingValidationOrchestrationService.wrap_direct_answer(
                        str(direct_answer or ""),
                        package=package,
                    ),
                    "drawingAnalysis": package.get("drawingAnalysis"),
                    "drawingAnalysisExport": export_payload,
                }

            return None

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

            humanized = self._presenter.present(data, path=path or "")

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

    def _try_sql_error_recovery(
            self,
            *,
            user_id: str,
            access_token: str,
            allowed_action_ids: list[str] | None,
            selected_tool: dict,
            metadata: dict,
            safe_tool_calls: list[dict],
            context_blocks: list[str],
            on_stream_activity=None,
        ):
            if not self._external_action_repository or not allowed_action_ids:
                return None

            from app.application.services.chat_sql_recovery_service import (
                ChatSqlRecoveryService,
            )

            recovery_service = ChatSqlRecoveryService(
                self._execute_tool_use_case,
                self._external_action_repository,
            )
            recovery = recovery_service.maybe_recover(
                user_id=user_id,
                access_token=access_token,
                allowed_action_ids=allowed_action_ids,
                arguments=selected_tool.get("arguments") or {},
                metadata=metadata,
                reason=selected_tool.get("reason"),
                on_stream_activity=on_stream_activity,
            )

            if not recovery:
                return None

            failed_metadata = self._formatter._build_safe_tool_metadata(
                tool_name="execute_external_action",
                metadata=recovery.failed_metadata,
                data=None,
            )
            safe_tool_calls.append(
                {
                    "name": "execute_external_action",
                    "arguments": recovery.failed_arguments,
                    "reason": selected_tool.get("reason"),
                    "metadata": failed_metadata,
                }
            )
            context_blocks.append(
                self._formatter._format_tool_context(
                    name="execute_external_action",
                    reason=selected_tool.get("reason"),
                    data=None,
                    metadata=recovery.failed_metadata,
                )
            )

            schema_metadata = self._formatter._build_safe_tool_metadata(
                tool_name="execute_external_action",
                metadata=recovery.schema_metadata,
                data=recovery.schema_data,
            )
            schema_reason = ChatToolContextContentService.format(
                "sqlRecovery",
                "schemaPrefetchReason",
                table_name=recovery.plan.table_name,
            )
            safe_tool_calls.append(
                {
                    "name": "execute_external_action",
                    "arguments": {
                        "parameters": {"tableName": recovery.plan.table_name},
                    },
                    "reason": schema_reason,
                    "metadata": schema_metadata,
                }
            )
            context_blocks.append(
                self._formatter._format_tool_context(
                    name="execute_external_action",
                    reason=schema_reason,
                    data=recovery.schema_data,
                    metadata=recovery.schema_metadata,
                )
            )

            return recovery
