"""Seleção de tools e external actions — Fase 3C lote 12."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.application.services.chat_tool_context_content_service import (
    ChatToolContextContentService,
)
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_product_query_intent_service import ChatProductQueryIntent
from app.infrastructure.config.settings import Settings

if TYPE_CHECKING:
    from app.application.services.chat_tool_context_service import ChatToolContextService


@dataclass
class ToolSelectionOutcome:
    early_result: dict | None = None
    selected_tools: list[dict] = field(default_factory=list)
    native_meta: dict = field(
        default_factory=lambda: {"used": False, "providerSupports": False}
    )
    selected_external_action_meta: dict | None = None


class ChatToolContextSelectionService:
    def select_tools(
        self,
        host: ChatToolContextService,
        *,
        message: str,
        raw_message: str,
        allowed_action_ids: list[str] | None,
        actions_enabled: bool,
        allowed_tool_names: list[str] | None,
        conversation_context: str | None,
        previous_messages: list | None,
        max_external_action_calls: int | None,
        on_stream_activity,
        agent_context: dict | None,
        attachment_context: str | None,
        drawing_analysis_mode: bool,
        drawing_product_code: str | None,
        drawing_product_code_source: str | None,
        drawing_runtime_skills: dict | None,
        drawing_pdf_extract: dict | None,
        web_search_exclusive: bool,
    ) -> ToolSelectionOutcome:
        native_meta = {"used": False, "providerSupports": False}
        native_selections: list[dict] = []

        if host.native_tool_calling_service:
            native_result = host.native_tool_calling_service.select_tools(
                message=message,
                allowed_tool_names=allowed_tool_names,
                tools_registry=host.execute_tool_use_case.tools,
                agent_context=agent_context,
            )
            native_meta = native_result.get("meta") or native_meta
            native_selections = list(native_result.get("selections") or [])

        if native_selections:
            selected_tools = native_selections
        else:
            selected_tools = host.tool_selection_service.select_tools(
                message,
                attachment_context=attachment_context,
                previous_messages=previous_messages,
            )

        if allowed_tool_names:
            allowed = {str(item).strip() for item in allowed_tool_names if str(item).strip()}
            selected_tools = [
                item for item in selected_tools if str(item.get("name") or "") in allowed
            ]

        router_suggestion = {"tools": [], "actionId": None}

        if (
            host.tool_router_service
            and actions_enabled
            and not native_selections
            and not web_search_exclusive
        ):
            catalog_actions = []

            if host.external_action_repository and allowed_action_ids:
                catalog_actions = host.external_action_repository.find_candidate_actions(
                    message,
                    limit=Settings.CHAT_TOOL_ROUTER_MAX_ACTIONS,
                    allowed_action_ids=allowed_action_ids,
                )

            router_suggestion = host.tool_router_service.suggest(
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
                        "reason": ChatToolContextContentService.get("router", "toolSuggested"),
                    }
                )

        selected_external_action = None
        selected_external_action_meta = None
        drawing_action_required = bool(drawing_analysis_mode and drawing_product_code)

        if (
            host.external_action_selection_service
            and actions_enabled
            and not web_search_exclusive
        ):
            from app.application.services.chat_external_action_orchestration_service import (
                ChatExternalActionOrchestrationService,
            )

            if on_stream_activity:
                from app.application.services.chat_stream_activity_service import (
                    ChatStreamActivityService,
                )

                on_stream_activity(
                    ChatStreamActivityService.plan_step(
                        step=1,
                        total=1,
                        target=ChatToolContextContentService.get("planning", "openApiTarget"),
                        verb=ChatAssistantContentService.get(
                            "stream",
                            "activity",
                            "verbs",
                            "planning",
                        ),
                        state="active",
                        detail=ChatToolContextContentService.get(
                            "planning",
                            "selectingRoutesDetail",
                        ),
                    )
                )

            plan_workspace = dict(host._build_workspace_context or {})

            if drawing_runtime_skills:
                merged_skills = plan_workspace.get("skills")

                if isinstance(merged_skills, dict):
                    plan_workspace["skills"] = {**merged_skills, **drawing_runtime_skills}
                else:
                    plan_workspace["skills"] = dict(drawing_runtime_skills)

            planned_external_actions = ChatExternalActionOrchestrationService.plan_actions(
                host.external_action_selection_service,
                message=message,
                raw_message=raw_message,
                allowed_action_ids=allowed_action_ids or [],
                conversation_context=conversation_context,
                previous_messages=previous_messages,
                max_calls=max_external_action_calls,
                on_stream_activity=on_stream_activity,
                workspace_context=plan_workspace,
                forced_product_code=drawing_product_code if drawing_action_required else None,
                forced_intent=(
                    ChatProductQueryIntent.ANALYSER
                    if drawing_action_required
                    else None
                ),
                forced_reason=(
                    ChatToolContextContentService.get("drawing", "forcedAnalyserReason")
                    if drawing_action_required
                    else None
                ),
            )

            if planned_external_actions:
                selected_tools = [
                    item
                    for item in selected_tools
                    if str(item.get("name") or "") != "execute_external_action"
                ]
                selected_tools.extend(planned_external_actions)
                first = planned_external_actions[0]
                arguments = first.get("arguments") or {}
                selected_external_action = first
                selected_external_action_meta = {
                    "actionId": arguments.get("actionId") or arguments.get("action_id"),
                    "reason": first.get("reason"),
                    "plannedCount": len(planned_external_actions),
                }

                if drawing_action_required:
                    selected_external_action_meta["forcedBy"] = "drawing_analysis_pdf"
                    selected_external_action_meta["productCode"] = drawing_product_code
                    selected_external_action_meta[
                        "productCodeSource"
                    ] = drawing_product_code_source

        if drawing_action_required and not selected_external_action:
            return ToolSelectionOutcome(
                early_result=host._finalize_tool_context_result(
                    message=raw_message,
                    previous_messages=previous_messages,
                    result={
                        "context": "",
                        "toolCalls": [],
                        "nativeToolCalling": native_meta,
                        "directAnswer": ChatToolContextContentService.format(
                            "drawing",
                            "missingAuthorizedAnalyserAction",
                            product_code=drawing_product_code,
                        ),
                        "skipRag": True,
                        "drawingAnalysisMode": True,
                        "drawingPdfExtractSummary": host._auxiliary_service._build_drawing_pdf_extract_summary(
                            drawing_pdf_extract,
                            product_code_source=drawing_product_code_source,
                        ),
                        "currentMessage": raw_message,
                    },
                ),
            )

        if not selected_tools:
            from app.domain.services.chat_sql_inventory_query_service import (
                ChatSqlInventoryQueryService,
            )
            from app.domain.services.chat_sql_production_query_service import (
                ChatSqlProductionQueryService,
            )

            for resolver in (
                ChatSqlProductionQueryService,
                ChatSqlInventoryQueryService,
            ):
                sql_resolution = resolver.resolve(message)

                if sql_resolution and sql_resolution.mode == "authoring":
                    return ToolSelectionOutcome(
                        early_result=host._finalize_tool_context_result(
                            message=raw_message,
                            previous_messages=previous_messages,
                            result={
                                "context": "",
                                "toolCalls": [],
                                "nativeToolCalling": native_meta,
                                "directAnswer": resolver.format_authoring_answer(
                                    sql_resolution
                                ),
                                "skipRag": True,
                                "currentMessage": raw_message,
                            },
                        ),
                    )

        if (
            actions_enabled
            and not web_search_exclusive
            and not selected_external_action
            and router_suggestion.get("actionId")
            and allowed_action_ids
            and str(router_suggestion["actionId"]) in {str(item) for item in allowed_action_ids}
        ):
            from app.domain.services.chat_analysis_intent_service import (
                ChatAnalysisIntentService,
            )
            from app.domain.services.chat_sql_operational_intent_service import (
                ChatSqlOperationalIntentService,
            )
            from app.domain.services.external_actions.external_action_sql_capability_service import (
                ExternalActionSqlCapabilityService,
            )

            router_action_id = str(router_suggestion["actionId"])
            skip_router_action = (
                ChatAnalysisIntentService.is_data_interpretation_request(
                    raw_message,
                    previous_messages,
                )
                or ExternalActionSqlCapabilityService.is_sql_execution_context(
                    action_id=router_action_id,
                )
            )

            if not skip_router_action and not ChatSqlOperationalIntentService.requires_sql_knowledge(message):
                selected_tools.append(
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": router_action_id,
                            "body": {"message": message},
                        },
                        "reason": ChatToolContextContentService.get("router", "actionSuggested"),
                    }
                )

        blocked_external_action = False

        if allowed_action_ids is not None:
            before_count = len(selected_tools)
            selected_tools = [
                tool
                for tool in selected_tools
                if str(tool.get("name") or "") != "execute_external_action"
                or host._is_external_action_allowed(tool, allowed_action_ids)
            ]
            blocked_external_action = before_count > 0 and not selected_tools

        if not selected_tools:
            early_result = {
                "context": "",
                "toolCalls": [],
                "nativeToolCalling": native_meta,
                "currentMessage": raw_message,
            }

            if blocked_external_action:
                early_result["suppressAdvancedSqlEnrichment"] = True

            return ToolSelectionOutcome(
                early_result=host._finalize_tool_context_result(
                    message=raw_message,
                    previous_messages=previous_messages,
                    result=early_result,
                ),
            )

        return ToolSelectionOutcome(
            selected_tools=selected_tools,
            native_meta=native_meta,
            selected_external_action_meta=selected_external_action_meta,
        )
