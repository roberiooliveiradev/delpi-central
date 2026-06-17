"""Atalho pré-turno: agrupamento local sobre payload retido na sessão."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from app.domain.services.chat_operational_group_by_refinement_service import (
    ChatOperationalGroupByRefinementService,
)
from app.domain.services.chat_operational_session_data_refinement_service import (
    ChatOperationalSessionDataRefinementService,
)
from app.domain.services.chat_presentation_format_refinement_service import (
    ChatPresentationFormatRefinementService,
)
from app.domain.services.chat_tabular_data_aggregation_service import (
    ChatTabularDataAggregationService,
)


@dataclass(frozen=True)
class GroupBySessionRefinementResult:
    kind: Literal["skip", "success", "failure"]
    payload: tuple[object, dict, dict, str | None] | None = None
    direct_answer: str | None = None


class ChatOperationalGroupBySessionRefinementService:
    @classmethod
    def resolve_turn(
        cls,
        message: str,
        *,
        previous_messages: list | None,
        external_use_case,
    ) -> GroupBySessionRefinementResult:
        plan = ChatOperationalGroupByRefinementService.plan_session_follow_up(
            message,
            previous_messages=previous_messages,
        )

        if not plan:
            return GroupBySessionRefinementResult(kind="skip")

        route = next(
            (
                item
                for item in ChatOperationalGroupByRefinementService.routes()
                if str(item.get("id") or "") == plan.route_id
            ),
            None,
        )

        if not route:
            return GroupBySessionRefinementResult(kind="skip")

        operation = ChatPresentationFormatRefinementService.collect_last_successful_operation(
            previous_messages,
        )

        if not operation:
            return GroupBySessionRefinementResult(kind="skip")

        wrapped = ChatPresentationFormatRefinementService.resolve_payload(
            previous_messages,
            operation=operation,
        )

        if wrapped is None:
            return GroupBySessionRefinementResult(kind="skip")

        root = cls._unwrap_payload(wrapped)
        source_rows = ChatTabularDataAggregationService.extract_items(root)

        if not source_rows:
            return GroupBySessionRefinementResult(kind="skip")

        dimension_entry = ChatOperationalGroupByRefinementService.dimension_entry(
            route,
            plan.dimension,
        )
        limit = cls._resolve_limit(plan.parameters)
        transformed_items = ChatOperationalSessionDataRefinementService.transform_items(
            source_rows,
            dimension_entry,
            limit=limit,
        )

        if not transformed_items:
            return GroupBySessionRefinementResult(kind="skip")

        if not isinstance(root, dict):
            root = {"items": source_rows}

        transformed_root = ChatOperationalSessionDataRefinementService.build_transformed_root(
            root,
            transformed_items,
        )
        payload = ChatPresentationFormatRefinementService.wrap_payload_for_operation(
            operation,
            transformed_root,
        )

        parameters = dict(operation.get("parameters") or {})
        parameters["sessionDataRefinement"] = (
            ChatOperationalSessionDataRefinementService.session_refinement_metadata(
                dimension=plan.dimension,
                dimension_label=plan.dimension_label,
                source_row_count=len(source_rows),
                result_row_count=len(transformed_items),
            )
        )

        if external_use_case is None:
            return GroupBySessionRefinementResult(kind="skip")

        rebuilt = ChatPresentationFormatRefinementService.rebuild_metadata_for_refinement(
            external_use_case=external_use_case,
            operation=operation,
            payload=payload,
            requested_format=str(parameters.get("sessionResponseFormat") or "").strip() or None,
            user_message=message,
        )

        if not rebuilt:
            return GroupBySessionRefinementResult(kind="skip")

        session_meta = parameters["sessionDataRefinement"]
        rebuilt["sessionDataRefinement"] = session_meta
        rebuilt["dataCoverageNotice"] = cls._build_sample_coverage_notice(
            session_meta=session_meta,
        )

        arguments = {
            "actionId": str(operation.get("actionId") or plan.action_id).strip(),
            "parameters": parameters,
        }

        return GroupBySessionRefinementResult(
            kind="success",
            payload=(payload, rebuilt, arguments, None),
        )

    @classmethod
    def _unwrap_payload(cls, wrapped: object) -> dict[str, Any]:
        if isinstance(wrapped, dict) and isinstance(wrapped.get("data"), dict):
            return dict(wrapped["data"])

        if isinstance(wrapped, dict):
            return dict(wrapped)

        return {}

    @classmethod
    def _resolve_limit(cls, parameters: dict[str, Any]) -> int | None:
        for key in ("limit", "page_size", "pagesize"):
            raw = parameters.get(key)

            try:
                value = int(raw)
            except (TypeError, ValueError):
                continue

            if value >= 1:
                return value

        return None

    @classmethod
    def _build_sample_coverage_notice(cls, *, session_meta: dict[str, Any]) -> dict[str, Any]:
        from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

        message = ChatAssistantContentService.format(
            "data_coverage",
            "sessionAggregateSample",
            shown=session_meta.get("sourceRowCount", 0),
            dimension=session_meta.get("dimensionLabel") or session_meta.get("dimension") or "",
        )

        return {
            "kind": "partial",
            "message": message,
            "details": {
                "sessionDataRefinement": session_meta,
            },
        }

    @classmethod
    def _build_sample_coverage_notice(cls, *, session_meta: dict[str, Any]) -> dict[str, Any]:
        from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

        message = ChatAssistantContentService.format(
            "data_coverage",
            "sessionAggregateSample",
            shown=session_meta.get("sourceRowCount", 0),
            dimension=session_meta.get("dimensionLabel") or session_meta.get("dimension") or "",
        )

        return {
            "kind": "partial",
            "message": message,
            "details": {
                "sessionDataRefinement": session_meta,
            },
        }
