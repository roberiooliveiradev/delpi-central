"""Follow-up operacional: reagrupar consulta anterior por dimensão configurável (JSON)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_operational_session_data_refinement_service import (
    ChatOperationalSessionDataRefinementService,
)
from app.domain.services.chat_presentation_format_refinement_service import (
    ChatPresentationFormatRefinementService,
)
from app.domain.services.chat_tabular_data_aggregation_service import (
    ChatTabularDataAggregationService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


@dataclass(frozen=True)
class OperationalGroupByRecentAction:
    action_id: str
    path: str
    parameters: dict[str, Any]
    route_id: str


@dataclass(frozen=True)
class OperationalGroupByPlan:
    route_id: str
    action_id: str
    path: str
    parameters: dict[str, Any]
    dimension: str
    dimension_label: str
    parameter_name: str
    execution_path: str
    refetch_group_by: str | None = None


class ChatOperationalGroupByRefinementService:
    BUNDLE = "operational_group_by_refinement"

    @classmethod
    @lru_cache(maxsize=1)
    def _content(cls) -> dict[str, Any]:
        payload = ChatAssistantContentService.load_bundle(cls.BUNDLE)

        if not isinstance(payload, dict):
            return {}

        return payload

    @classmethod
    def invalidate_cache(cls) -> None:
        cls._content.cache_clear()

    @classmethod
    def routes(cls) -> list[dict[str, Any]]:
        routes = cls._content().get("routes")

        if not isinstance(routes, list):
            return []

        return [route for route in routes if isinstance(route, dict)]

    @classmethod
    def chart_axis_fields(cls) -> tuple[str, ...]:
        fields = cls._content().get("chartAxisFields")

        if not isinstance(fields, list):
            return ()

        return tuple(str(item).strip() for item in fields if str(item).strip())

    @classmethod
    def aggregate_phrases(cls) -> tuple[str, ...]:
        phrases = cls._content().get("aggregatePhrases")

        if not isinstance(phrases, list):
            return ()

        return tuple(str(item).strip().lower() for item in phrases if str(item).strip())

    @classmethod
    def list_context_phrases(cls) -> tuple[str, ...]:
        phrases = cls._content().get("listContextPhrases")

        if not isinstance(phrases, list):
            return ()

        return tuple(str(item).strip().lower() for item in phrases if str(item).strip())

    @classmethod
    def match_route_for_path(cls, path: str) -> dict[str, Any] | None:
        lowered = str(path or "").lower()

        for route in cls.routes():
            marker = str(route.get("pathContains") or "").strip().lower()

            if not marker or marker not in lowered:
                continue

            excluded = route.get("pathExcludeContains") or []

            if isinstance(excluded, list) and any(
                str(fragment).strip().lower() in lowered
                for fragment in excluded
                if str(fragment).strip()
            ):
                continue

            return route

        return None

    @classmethod
    def match_route_for_context(cls, conversation_context: str | None) -> dict[str, Any] | None:
        return cls.match_route_for_path(str(conversation_context or ""))

    @classmethod
    def route_dimensions(cls, route: dict[str, Any]) -> list[dict[str, Any]]:
        dimensions = route.get("dimensions")

        if not isinstance(dimensions, list):
            return []

        return [item for item in dimensions if isinstance(item, dict)]

    @classmethod
    def dimension_label(cls, route: dict[str, Any], dimension: str) -> str:
        target = str(dimension or "").strip().lower()

        for entry in cls.route_dimensions(route):
            if str(entry.get("value") or "").strip().lower() != target:
                continue

            label = str(entry.get("label") or "").strip()

            if label:
                return label

        return target

    @classmethod
    def dimension_entry(cls, route: dict[str, Any], dimension: str) -> dict[str, Any]:
        return ChatOperationalSessionDataRefinementService.dimension_config(route, dimension)

    @classmethod
    def resolve_rows_from_session(
        cls,
        previous_messages: list[Any] | None,
        *,
        recent: OperationalGroupByRecentAction,
    ) -> list[dict[str, Any]]:
        operation = {
            "actionId": recent.action_id,
            "path": recent.path,
            "parameters": dict(recent.parameters),
            "metadata": {},
        }

        for item in reversed((previous_messages or [])[-14:]):
            metadata = cls._message_metadata(item)

            for tool_call in reversed(metadata.get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if str(tool_meta.get("path") or "") != recent.path:
                    continue

                operation["metadata"] = dict(tool_meta)
                break

        payload = ChatPresentationFormatRefinementService.resolve_payload(
            previous_messages,
            operation=operation,
        )

        if payload is None:
            return []

        root = payload.get("data") if isinstance(payload, dict) else payload

        return ChatTabularDataAggregationService.extract_items(root)

    @classmethod
    def resolve_dimension(cls, normalized: str, route: dict[str, Any]) -> str | None:
        matches: list[tuple[int, str]] = []

        for entry in cls.route_dimensions(route):
            value = str(entry.get("value") or "").strip().lower()

            if not value:
                continue

            terms = entry.get("terms") or []

            if not isinstance(terms, list):
                continue

            for term in terms:
                token = str(term or "").strip().lower()

                if token and token in normalized:
                    matches.append((len(token), value))

        if not matches:
            return None

        matches.sort(key=lambda item: item[0], reverse=True)
        return matches[0][1]

    @classmethod
    def looks_like_group_by_refinement(cls, normalized: str, *, route: dict[str, Any] | None = None) -> bool:
        if cls.resolve_dimension(normalized, route) if route else None:
            return True

        if not ChatMessageNormalizationService.contains_any(
            normalized,
            cls.aggregate_phrases(),
        ):
            return False

        if route and cls.resolve_dimension(normalized, route):
            return True

        if ChatMessageNormalizationService.contains_any(
            normalized,
            cls.list_context_phrases(),
        ):
            return True

        return any(
            token in normalized
            for token in (
                "agrup",
                "consumo",
                "consome",
                "ranking",
                "total",
                "soma",
            )
        )

    @classmethod
    def collect_recent_action(
        cls,
        previous_messages: list[Any] | None,
        *,
        conversation_context: str | None = None,
    ) -> OperationalGroupByRecentAction | None:
        for item in reversed((previous_messages or [])[-14:]):
            metadata = cls._message_metadata(item)

            for tool_call in reversed(metadata.get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if not tool_meta.get("ok"):
                    continue

                path = str(tool_meta.get("path") or "")
                route = cls.match_route_for_path(path)

                if not route:
                    continue

                arguments = tool_call.get("arguments") or {}
                parameters = arguments.get("parameters") or {}

                if not isinstance(parameters, dict):
                    parameters = {}

                action_id = str(
                    tool_meta.get("actionId")
                    or arguments.get("actionId")
                    or route.get("actionIdDefault")
                    or ""
                ).strip()

                if not action_id:
                    continue

                return OperationalGroupByRecentAction(
                    action_id=action_id,
                    path=path,
                    parameters=dict(parameters),
                    route_id=str(route.get("id") or "").strip(),
                )

        route = cls.match_route_for_context(conversation_context)

        if not route:
            return None

        return OperationalGroupByRecentAction(
            action_id=str(route.get("actionIdDefault") or "").strip(),
            path=str(route.get("pathContains") or "").strip(),
            parameters={},
            route_id=str(route.get("id") or "").strip(),
        )

    @classmethod
    def plan_follow_up(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> OperationalGroupByPlan | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        recent = cls.collect_recent_action(
            previous_messages,
            conversation_context=conversation_context,
        )

        if not recent:
            return None

        route = next(
            (item for item in cls.routes() if str(item.get("id") or "") == recent.route_id),
            None,
        )

        if not route:
            route = cls.match_route_for_path(recent.path)

        if not route:
            return None

        if not cls.looks_like_group_by_refinement(normalized, route=route):
            return None

        dimension = cls.resolve_dimension(normalized, route)

        if not dimension:
            return None

        parameter_name = str(route.get("parameterName") or "group_by").strip()
        current = cls._parameter_str(recent.parameters, parameter_name) or str(
            route.get("defaultDimension") or "general"
        )
        current = current.strip().lower()

        if current == dimension:
            return None

        dimension_entry = cls.dimension_entry(route, dimension)
        rows = cls.resolve_rows_from_session(
            previous_messages,
            recent=recent,
        )
        execution_path = ChatOperationalSessionDataRefinementService.resolve_execution_path(
            dimension_entry,
            rows,
        )

        if execution_path == "skip":
            return None

        refetch_group_by = None

        if execution_path == "refetch":
            refetch_group_by = ChatOperationalSessionDataRefinementService.refetch_group_by_value(
                dimension_entry,
                dimension=dimension,
            )

        return OperationalGroupByPlan(
            route_id=str(route.get("id") or "").strip(),
            action_id=recent.action_id,
            path=recent.path,
            parameters=dict(recent.parameters),
            dimension=dimension,
            dimension_label=cls.dimension_label(route, dimension),
            parameter_name=parameter_name,
            execution_path=execution_path,
            refetch_group_by=refetch_group_by,
        )

    @classmethod
    def plan_refetch_follow_up(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> OperationalGroupByPlan | None:
        plan = cls.plan_follow_up(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

        if not plan or plan.execution_path != "refetch":
            return None

        return plan

    @classmethod
    def plan_session_follow_up(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> OperationalGroupByPlan | None:
        plan = cls.plan_follow_up(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

        if not plan or plan.execution_path != "session":
            return None

        return plan

    @classmethod
    def _parameter_str(cls, parameters: dict[str, Any], key: str) -> str | None:
        for name, value in parameters.items():
            if str(name).lower() != key.lower():
                continue

            raw = str(value or "").strip()

            if raw:
                return raw

        return None

    @classmethod
    def _message_metadata(cls, message: Any) -> dict[str, Any]:
        if isinstance(message, dict):
            metadata = message.get("metadata")
            return metadata if isinstance(metadata, dict) else {}

        metadata = getattr(message, "metadata", None)
        return metadata if isinstance(metadata, dict) else {}
