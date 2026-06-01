"""Busca páginas adicionais e consolida respostas paginadas da API."""

from __future__ import annotations

from app.application.dto.execute_tool_request import ExecuteToolRequest
from app.application.use_cases.execute_tool_use_case import ExecuteToolUseCase
from app.domain.services.chat_pagination_consolidation_service import (
    ChatPaginationConsolidationService,
    PaginationFetchPlan,
)


class ChatPaginatedExternalActionService:
    def __init__(self, execute_tool_use_case: ExecuteToolUseCase):
        self.execute_tool_use_case = execute_tool_use_case

    def fetch_continue_plan(
        self,
        *,
        user_id: str,
        access_token: str,
        message: str,
        previous_messages: list | None,
        on_stream_activity=None,
    ) -> tuple[object, dict, dict, str | None] | None:
        plan = ChatPaginationConsolidationService.build_continue_plan(
            message=message,
            previous_messages=previous_messages,
        )

        if not plan:
            return None

        cached = ChatPaginationConsolidationService.load_cached_payload(previous_messages)
        merged_data, merged_metadata, continue_prompt = self._fetch_pages(
            user_id=user_id,
            access_token=access_token,
            plan=plan,
            base_data=None,
            base_metadata={},
            base_arguments={
                "actionId": plan.action_id,
                "parameters": plan.base_parameters,
            },
            cached=cached,
            initial_pages=list(plan.resume_state.fetched_pages if plan.resume_state else []),
            on_stream_activity=on_stream_activity,
        )

        arguments = {
            "actionId": plan.action_id,
            "parameters": dict(plan.base_parameters),
        }

        return merged_data, merged_metadata, arguments, continue_prompt

    def fetch_full_from_history(
        self,
        *,
        user_id: str,
        access_token: str,
        message: str,
        previous_messages: list | None,
        on_stream_activity=None,
    ) -> tuple[object, dict, dict, str | None] | None:
        if not ChatPaginationConsolidationService.looks_like_full_fetch_request(message):
            return None

        if ChatPaginationConsolidationService.collect_state(previous_messages):
            return None

        reference = ChatPaginationConsolidationService.collect_last_paginated_reference(
            previous_messages,
        )

        if not reference:
            return None

        action_id = reference["actionId"]
        parameters = dict(reference["parameters"])
        parameters["page"] = 1

        try:
            result = self.execute_tool_use_case.execute(
                ExecuteToolRequest(
                    user_id=user_id,
                    access_token=access_token,
                    tool_name="execute_external_action",
                    arguments={
                        "actionId": action_id,
                        "parameters": parameters,
                    },
                )
            )
        except Exception:
            return None

        metadata = dict(result.metadata or {})

        if not metadata.get("ok"):
            return None

        merged_data, merged_metadata, continue_prompt = self.maybe_consolidate(
            user_id=user_id,
            access_token=access_token,
            message=message,
            previous_messages=previous_messages,
            base_arguments={
                "actionId": action_id,
                "parameters": parameters,
            },
            base_metadata=metadata,
            base_data=result.data,
            on_stream_activity=on_stream_activity,
        )

        arguments = {
            "actionId": action_id,
            "parameters": parameters,
        }

        return merged_data, merged_metadata, arguments, continue_prompt

    def fetch_format_refinement_from_history(
        self,
        *,
        user_id: str,
        access_token: str,
        message: str,
        previous_messages: list | None,
        on_stream_activity=None,
    ) -> tuple[object, dict, dict, str | None] | None:
        from app.domain.services.chat_presentation_format_refinement_service import (
            ChatPresentationFormatRefinementService,
        )

        if not ChatPresentationFormatRefinementService.looks_like_format_refinement(message):
            return None

        operation = ChatPresentationFormatRefinementService.collect_last_successful_operation(
            previous_messages,
        )

        if not operation:
            return None

        action_id = str(operation.get("actionId") or "").strip()
        parameters = dict(operation.get("parameters") or {})
        path = str(operation.get("path") or "")

        if not action_id and not path:
            return None

        payload = ChatPresentationFormatRefinementService.resolve_payload(
            previous_messages,
            operation=operation,
        )

        if payload is None and action_id:
            try:
                result = self.execute_tool_use_case.execute(
                    ExecuteToolRequest(
                        user_id=user_id,
                        access_token=access_token,
                        tool_name="execute_external_action",
                        arguments={
                            "actionId": action_id,
                            "parameters": parameters,
                        },
                    )
                )
            except Exception:
                return None

            if not (result.metadata or {}).get("ok"):
                return None

            payload = result.data
            base_metadata = dict(result.metadata or {})
        else:
            base_metadata = dict(operation.get("metadata") or {})

        if payload is None:
            return None

        arguments = {
            "actionId": action_id,
            "parameters": parameters,
        }

        return payload, base_metadata, arguments, None

    def fetch_error_recovery_from_history(
        self,
        *,
        user_id: str,
        access_token: str,
        message: str,
        previous_messages: list | None,
        on_stream_activity=None,
    ) -> tuple[object, dict, dict, str | None] | None:
        from app.domain.services.chat_error_auto_recovery_service import (
            ChatErrorAutoRecoveryService,
        )

        if not ChatErrorAutoRecoveryService.looks_like_recovery_request(message):
            return None

        strategy = ChatErrorAutoRecoveryService.resolve_strategy(message)
        operation = ChatErrorAutoRecoveryService.collect_operation(
            None,
            previous_messages=previous_messages,
            prefer_failed=True,
        )

        if not operation:
            operation = ChatErrorAutoRecoveryService.collect_operation(
                None,
                previous_messages=previous_messages,
                prefer_failed=False,
            )

        if not operation:
            return None

        action_id = str(operation.get("actionId") or "").strip()
        parameters = ChatErrorAutoRecoveryService.apply_strategy(
            strategy,
            operation,
            message,
        )

        if not action_id:
            return None

        try:
            result = self.execute_tool_use_case.execute(
                ExecuteToolRequest(
                    user_id=user_id,
                    access_token=access_token,
                    tool_name="execute_external_action",
                    arguments={
                        "actionId": action_id,
                        "parameters": parameters,
                    },
                )
            )
        except Exception:
            return None

        if not (result.metadata or {}).get("ok"):
            return None

        arguments = {
            "actionId": action_id,
            "parameters": parameters,
        }

        audit_meta = dict(result.metadata or {})
        audit_meta["errorRecoveryAttempt"] = {
            "strategy": strategy,
            "ok": True,
        }

        return result.data, audit_meta, arguments, None

    def maybe_consolidate(
        self,
        *,
        user_id: str,
        access_token: str,
        message: str,
        previous_messages: list | None,
        base_arguments: dict,
        base_metadata: dict,
        base_data: object,
        on_stream_activity=None,
    ) -> tuple[object, dict, str | None]:
        plan = ChatPaginationConsolidationService.build_fetch_plan(
            message=message,
            metadata=base_metadata,
            data=base_data,
            arguments=base_arguments,
            previous_messages=previous_messages,
        )

        if not plan or not plan.pages_to_fetch:
            return base_data, base_metadata, None

        cached = ChatPaginationConsolidationService.load_cached_payload(previous_messages)
        snapshot = ChatPaginationConsolidationService.extract_snapshot(
            metadata=base_metadata,
            data=base_data,
        )
        initial_pages = [snapshot.page if snapshot else 1]

        return self._fetch_pages(
            user_id=user_id,
            access_token=access_token,
            plan=plan,
            base_data=base_data,
            base_metadata=base_metadata,
            base_arguments=base_arguments,
            cached=cached,
            initial_pages=initial_pages,
            on_stream_activity=on_stream_activity,
        )

    def _fetch_pages(
        self,
        *,
        user_id: str,
        access_token: str,
        plan: PaginationFetchPlan,
        base_data: object | None,
        base_metadata: dict,
        base_arguments: dict,
        cached: dict | None,
        initial_pages: list[int],
        on_stream_activity=None,
    ) -> tuple[object, dict, str | None]:
        action_id = plan.action_id or str(
            base_arguments.get("actionId") or base_arguments.get("action_id") or ""
        )

        if not action_id:
            return base_data or {}, base_metadata, None

        payloads = [base_data] if base_data is not None else []
        fetched_pages = list(initial_pages)
        total_pages = plan.resume_state.total_pages if plan.resume_state else None
        api_total = plan.resume_state.api_total if plan.resume_state else None

        snapshot = None

        if base_data is not None:
            snapshot = ChatPaginationConsolidationService.extract_snapshot(
                metadata=base_metadata,
                data=base_data,
            )

            if snapshot:
                total_pages = snapshot.total_pages or total_pages
                api_total = snapshot.total or api_total

        external_use_case = self._external_action_use_case()

        for index, page in enumerate(plan.pages_to_fetch, start=1):
            if on_stream_activity:
                from app.application.services.chat_stream_activity_service import (
                    ChatStreamActivityService,
                )

                on_stream_activity(
                    ChatStreamActivityService.tool_started(
                        index=index,
                        total=len(plan.pages_to_fetch),
                        path=plan.path or None,
                        action_id=action_id,
                        reason=f"Consolidando página {page}.",
                    )
                )

            parameters = dict(plan.base_parameters)
            parameters["page"] = page

            try:
                result = self.execute_tool_use_case.execute(
                    ExecuteToolRequest(
                        user_id=user_id,
                        access_token=access_token,
                        tool_name="execute_external_action",
                        arguments={
                            "actionId": action_id,
                            "parameters": parameters,
                        },
                    )
                )
            except Exception:
                break

            metadata = result.metadata or {}

            if on_stream_activity:
                from app.application.services.chat_stream_activity_service import (
                    ChatStreamActivityService,
                )

                on_stream_activity(
                    ChatStreamActivityService.tool_finished(
                        index=index,
                        total=len(plan.pages_to_fetch),
                        metadata=metadata,
                        path=str(metadata.get("path") or plan.path or "") or None,
                        action_id=action_id,
                        data=result.data,
                    )
                )

            if not metadata.get("ok"):
                break

            payloads.append(result.data)
            fetched_pages.append(page)

            page_snapshot = ChatPaginationConsolidationService.extract_snapshot(
                metadata=metadata,
                data=result.data,
            )

            if page_snapshot:
                total_pages = page_snapshot.total_pages or total_pages
                api_total = page_snapshot.total or api_total

        merged_data = ChatPaginationConsolidationService.merge_payloads(
            payloads,
            cached=cached,
        )
        merged_count = len(ChatPaginationConsolidationService._unwrap_items(merged_data))

        state = ChatPaginationConsolidationService.build_state(
            plan=plan,
            fetched_pages=fetched_pages,
            merged_count=merged_count,
            api_total=api_total,
            total_pages=total_pages,
        )

        merged_metadata = dict(base_metadata)

        if external_use_case is not None:
            rebuilt = external_use_case.build_metadata_for_data(
                action_id=action_id,
                data=merged_data,
                parameters=dict(plan.base_parameters),
            )
            merged_metadata.update(rebuilt)
        else:
            merged_metadata["dataCoverageNotice"] = None

        merged_metadata["paginationConsolidation"] = (
            ChatPaginationConsolidationService.state_to_metadata(
                state,
                merged_data=merged_data,
            )
        )

        continue_prompt = None

        if not state.completed:
            continue_prompt = ChatPaginationConsolidationService.build_continue_prompt(
                state=state,
            )

        return merged_data, merged_metadata, continue_prompt

    def _external_action_use_case(self):
        tools = getattr(self.execute_tool_use_case, "tools", None)

        if not isinstance(tools, dict):
            return None

        tool = tools.get("execute_external_action")

        if tool is None:
            return None

        return getattr(tool, "use_case", None)
