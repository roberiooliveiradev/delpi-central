"""Execução do loop de tools — Fase 3C lote 12."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from app.application.dto.execute_tool_request import ExecuteToolRequest
from app.application.services.chat_tool_context_content_service import (
    ChatToolContextContentService,
)
from app.application.services.chat_tool_context_format_service import (
    ChatToolContextFormatService,
)
from app.domain.entities.tool_result import ToolResult
from app.domain.services.chat_platform_internal_tools_service import (
    PLATFORM_INTERNAL_TOOL_NAMES,
    ChatPlatformInternalToolsService,
)
from app.infrastructure.config.settings import Settings

if TYPE_CHECKING:
    from app.application.services.chat_paginated_external_action_service import (
        ChatPaginatedExternalActionService,
    )
    from app.application.services.chat_tool_context_service import ChatToolContextService


@dataclass
class ToolExecutionState:
    context: str = ""
    safe_tool_calls: list[dict] = field(default_factory=list)
    direct_answer: str | None = None
    skip_rag: bool = False
    last_external_action_data: Any = None
    last_web_search_data: dict | None = None
    last_platform_tool_result: tuple[str, Any, dict] | None = None
    web_sources: list[dict] = field(default_factory=list)
    web_search_payload: dict | None = None
    external_action_results: list = field(default_factory=list)
    pagination_continue_prompt: str | None = None


class ChatToolContextExecutionService:
    def execute_selected_tools(
        self,
        host: ChatToolContextService,
        *,
        user_id: str,
        access_token: str,
        message: str,
        raw_message: str,
        allowed_action_ids: list[str] | None,
        previous_messages: list | None,
        selected_tools: list[dict],
        on_stream_activity,
        paginated_service: ChatPaginatedExternalActionService,
    ) -> ToolExecutionState:
        context_blocks: list[str] = []
        safe_tool_calls: list[dict] = []
        direct_answer: str | None = None
        skip_rag = False
        last_external_action_data = None
        last_web_search_data: dict | None = None
        last_platform_tool_result: tuple[str, Any, dict] | None = None
        web_sources: list[dict] = []
        web_search_payload: dict | None = None
        external_action_results: list = []
        external_planned = [
            item
            for item in selected_tools
            if str(item.get("name") or "") == "execute_external_action"
        ]
        external_total = len(external_planned)
        external_index = 0
        pagination_continue_prompt: str | None = None

        if on_stream_activity and external_total > 0:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            on_stream_activity(
                ChatStreamActivityService.entry(
                    verb="Executando",
                    target=ChatToolContextContentService.format(
                        "execution",
                        "externalActionsTarget",
                        count=str(external_total),
                    ),
                    phase="tools",
                    state="active",
                    message=ChatToolContextContentService.format(
                        "execution",
                        "externalActionsMessage",
                        count=str(external_total),
                    ),
                )
            )

        workspace_context = getattr(host, "_build_workspace_context", None)
        workspace_context = workspace_context if isinstance(workspace_context, dict) else None

        session_response_format = ChatToolContextFormatService.session_response_format(
            workspace_context,
        )

        for selected_tool in selected_tools:
            tool_name = str(selected_tool.get("name") or "")
            arguments = dict(selected_tool.get("arguments") or {})
            action_id = str(arguments.get("actionId") or arguments.get("action_id") or "")
            path_hint = str(arguments.get("path") or "")

            if tool_name == "execute_external_action" and session_response_format:
                parameters = dict(arguments.get("parameters") or {})
                parameters["sessionResponseFormat"] = session_response_format
                parameters.setdefault("userMessage", raw_message)
                arguments["parameters"] = parameters

            if tool_name == "execute_external_action":
                external_index += 1

                if on_stream_activity:
                    from app.application.services.chat_stream_activity_service import (
                        ChatStreamActivityService,
                    )

                    on_stream_activity(
                        ChatStreamActivityService.tool_started(
                            index=external_index,
                            total=external_total,
                            path=path_hint or None,
                            action_id=action_id or None,
                            reason=selected_tool.get("reason"),
                        )
                    )

            if tool_name == "web_search" and on_stream_activity:
                from app.application.services.chat_stream_activity_service import (
                    ChatStreamActivityService,
                )

                search_query = str(arguments.get("query") or raw_message or "").strip()

                on_stream_activity(
                    ChatStreamActivityService.web_search_started(query=search_query)
                )

            if (
                tool_name == "execute_external_action"
                and action_id
                and host.external_action_repository
            ):
                from app.domain.services.chat_write_confirmation_service import (
                    ChatWriteConfirmationService,
                )

                action_bundle = host.external_action_repository.get_action_for_execution(
                    action_id
                )
                action = (action_bundle or {}).get("action") if action_bundle else None

                if ChatWriteConfirmationService.should_block_execution(
                    message=raw_message,
                    action=action,
                ):
                    prompt = ChatWriteConfirmationService.confirmation_prompt(action)
                    direct_answer = direct_answer or prompt
                    skip_rag = True

                    blocked_metadata = {
                        "ok": False,
                        "blocked": True,
                        "blockReason": "confirmation_required",
                        "actionId": action_id,
                        "path": path_hint or str((action or {}).get("path") or ""),
                        "sensitivity": (action or {}).get("sensitivity"),
                    }
                    blocked_metadata["responsePreview"] = host._build_response_preview(
                        blocked_metadata
                    )

                    safe_tool_calls.append(
                        {
                            "name": tool_name,
                            "arguments": arguments,
                            "reason": selected_tool.get("reason"),
                            "metadata": blocked_metadata,
                        }
                    )

                    if on_stream_activity:
                        from app.application.services.chat_stream_activity_service import (
                            ChatStreamActivityService,
                        )

                        on_stream_activity(
                            ChatStreamActivityService.tool_finished(
                                index=external_index,
                                total=external_total,
                                metadata=blocked_metadata,
                                path=blocked_metadata.get("path"),
                                action_id=action_id,
                            )
                        )

                    continue

            try:
                result = host.execute_tool_use_case.execute(
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

                if tool_name == "execute_external_action" and on_stream_activity:
                    from app.application.services.chat_stream_activity_service import (
                        ChatStreamActivityService,
                    )

                    on_stream_activity(
                        ChatStreamActivityService.tool_finished(
                            index=external_index,
                            total=external_total,
                            metadata=error_metadata,
                            path=path_hint or None,
                            action_id=action_id or None,
                        )
                    )

                if tool_name == "execute_external_action":
                    error_metadata["responsePreview"] = host._build_response_preview(
                        error_metadata
                    )

                    from app.application.services.chat_composite_direct_answer_service import (
                        ExternalActionExecutionResult,
                    )

                    external_action_results.append(
                        ExternalActionExecutionResult(
                            metadata=error_metadata,
                            data=None,
                            reason=selected_tool.get("reason"),
                        )
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
                    host._format_tool_error_context(
                        name=tool_name,
                        reason=selected_tool.get("reason"),
                        error=exc,
                    )
                )
                continue

            result_data = result.data
            result_metadata = dict(result.metadata or {})

            if (
                result.name == "execute_external_action"
                and not host._is_successful_external_action(result_metadata)
            ):
                recovery = host._auxiliary_service._try_sql_error_recovery(
                    user_id=user_id,
                    access_token=access_token,
                    allowed_action_ids=allowed_action_ids,
                    selected_tool=selected_tool,
                    metadata=result_metadata,
                    safe_tool_calls=safe_tool_calls,
                    context_blocks=context_blocks,
                    on_stream_activity=on_stream_activity,
                )

                if recovery:
                    selected_tool = {
                        **selected_tool,
                        "reason": recovery.plan.reason,
                        "arguments": {
                            **(selected_tool.get("arguments") or {}),
                            "body": {
                                "sql": recovery.plan.corrected_sql,
                                "query": recovery.plan.corrected_sql,
                                "statement": recovery.plan.corrected_sql,
                            },
                        },
                    }
                    result_data = recovery.retry_data
                    result_metadata = dict(recovery.retry_metadata)
                    result = ToolResult(
                        name=result.name,
                        data=result_data,
                        metadata=result_metadata,
                    )

            if (
                result.name == "execute_external_action"
                and host._is_successful_external_action(result_metadata)
            ):
                (
                    result_data,
                    result_metadata,
                    pagination_continue_prompt,
                ) = paginated_service.maybe_consolidate(
                    user_id=user_id,
                    access_token=access_token,
                    message=raw_message,
                    previous_messages=previous_messages,
                    base_arguments=selected_tool.get("arguments") or {},
                    base_metadata=result_metadata,
                    base_data=result_data,
                    on_stream_activity=on_stream_activity,
                )
                result = ToolResult(
                    name=result.name,
                    data=result_data,
                    metadata=result_metadata,
                )

            safe_metadata = host._external_action_formatter._build_safe_tool_metadata(
                tool_name=result.name,
                metadata=result.metadata,
                data=result.data,
            )

            if result.name == "execute_external_action":
                from app.domain.services.chat_advanced_sql_specialist_service import (
                    ChatAdvancedSqlSpecialistService,
                )
                from app.domain.services.external_actions.external_action_sql_capability_service import (
                    ExternalActionSqlCapabilityService,
                )

                safe_metadata = ChatAdvancedSqlSpecialistService.annotate_schema_prefetch_tool_metadata(
                    raw_message,
                    safe_metadata,
                )

                executed_sql = ExternalActionSqlCapabilityService.extract_sql_from_arguments(
                    selected_tool.get("arguments")
                )
                if executed_sql:
                    safe_metadata["executedSql"] = executed_sql

            safe_tool_calls.append(
                {
                    "name": result.name,
                    "arguments": selected_tool.get("arguments") or {},
                    "reason": selected_tool.get("reason"),
                    "metadata": safe_metadata,
                }
            )

            if result.name in PLATFORM_INTERNAL_TOOL_NAMES:
                skip_rag = True

            if ChatPlatformInternalToolsService.is_direct_answer_tool(result.name):
                last_platform_tool_result = (
                    result.name,
                    result.data,
                    dict(safe_metadata),
                )
                from app.domain.services.chat_platform_tool_direct_answer_service import (
                    ChatPlatformToolDirectAnswerService,
                )

                platform_direct = ChatPlatformToolDirectAnswerService.format(
                    result.name,
                    data=result.data,
                    metadata=safe_metadata,
                    message=raw_message,
                )

                if platform_direct:
                    direct_answer = platform_direct

            if result.name == "execute_external_action":
                skip_rag = True

                if on_stream_activity:
                    from app.application.services.chat_stream_activity_service import (
                        ChatStreamActivityService,
                    )

                    on_stream_activity(
                        ChatStreamActivityService.tool_finished(
                            index=external_index,
                            total=external_total,
                            metadata=safe_metadata,
                            path=str(safe_metadata.get("path") or path_hint or "") or None,
                            action_id=str(safe_metadata.get("actionId") or action_id or "")
                            or None,
                            data=result.data,
                        )
                    )

                from app.application.services.chat_composite_direct_answer_service import (
                    ExternalActionExecutionResult,
                )

                external_action_results.append(
                    ExternalActionExecutionResult(
                        metadata=safe_metadata,
                        data=result.data,
                        reason=selected_tool.get("reason"),
                    )
                )

                if host._is_successful_external_action(safe_metadata):
                    last_external_action_data = result.data

            if result.name == "web_search" and isinstance(result.data, dict):
                if str(result.data.get("searchStatus") or "") in {"success", "no_results"}:
                    last_web_search_data = result.data

                if on_stream_activity:
                    from app.application.services.chat_stream_activity_service import (
                        ChatStreamActivityService,
                    )

                    on_stream_activity(
                        ChatStreamActivityService.web_search_finished(payload=result.data)
                    )

            context_blocks.append(
                host._external_action_formatter._format_tool_context(
                    name=result.name,
                    reason=selected_tool.get("reason"),
                    data=result.data,
                    metadata=safe_metadata,
                    arguments=selected_tool.get("arguments"),
                    message=raw_message,
                )
            )

        context = "\n\n".join(context_blocks)
        context = context[: Settings.MAX_CONTEXT_CHARS]

        return ToolExecutionState(
            context=context,
            safe_tool_calls=safe_tool_calls,
            direct_answer=direct_answer,
            skip_rag=skip_rag,
            last_external_action_data=last_external_action_data,
            last_web_search_data=last_web_search_data,
            last_platform_tool_result=last_platform_tool_result,
            web_sources=web_sources,
            web_search_payload=web_search_payload,
            external_action_results=external_action_results,
            pagination_continue_prompt=pagination_continue_prompt,
        )
