"""Planejamento de várias rotas para meta / indicadores departamentais."""

from __future__ import annotations

from typing import Any, Callable

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_api_domain_service import (
    ChatOperationalApiDomainService,
)
from app.domain.services.operational_api_parameter_builder_service import (
    OperationalApiParameterBuilderService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)

_BUNDLE = "department_meta_composition"


class ChatDepartmentMetaCompositionPlanningService:
    @classmethod
    def looks_like_department_meta_composition(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        triggers = ChatAssistantContentService.list(_BUNDLE, "triggerTerms")

        return any(str(term).strip() and str(term) in normalized for term in triggers)

    @classmethod
    def resolve_department_id(cls, message: str | None) -> str | None:
        spec = ChatOperationalApiDomainService.parameter_strategy_spec("department_idd")
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized or not isinstance(spec, dict):
            return None

        resolved = OperationalApiParameterBuilderService._resolve_source_value(
            "department_id_regex",
            {"source": "department_id_regex", "matchAliases": ["department_id"]},
            spec,
            {"normalized": normalized},
        )
        value = str(resolved or "").strip().lower()

        return value or None

    @classmethod
    def composition_mode(cls, message: str | None) -> str:
        """``primary`` (meta curta) vs ``compose`` (painel / indicadores / visão integrada)."""
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        default_mode = str(
            ChatAssistantContentService.get(_BUNDLE, "defaultMode", default="primary")
            or "primary"
        ).strip().lower()

        if default_mode not in {"primary", "compose"}:
            default_mode = "primary"

        if not normalized:
            return default_mode

        full_terms = ChatAssistantContentService.list(
            _BUNDLE,
            "composeModeTerms",
            "full",
        )

        if any(str(term).strip() and str(term) in normalized for term in full_terms):
            return "compose"

        return default_mode

    @classmethod
    def route_ids_for_department(
        cls,
        department_id: str,
        *,
        mode: str = "compose",
    ) -> list[str]:
        node = ChatAssistantContentService.get_node(
            _BUNDLE,
            "byDepartment",
            str(department_id or "").strip().lower(),
        )

        if not isinstance(node, dict):
            return []

        primary = str(node.get("primaryRouteId") or "").strip()
        compose = node.get("composeRouteIds") or []
        route_ids: list[str] = []

        if primary:
            route_ids.append(primary)

        if mode == "compose" and isinstance(compose, list):
            for item in compose:
                route_id = str(item or "").strip()

                if route_id and route_id not in route_ids:
                    route_ids.append(route_id)

        return route_ids

    @classmethod
    def plan(
        cls,
        selection_service: Any,
        *,
        message: str,
        allowed_action_ids: list[str] | None,
        previous_messages: list | None = None,
        max_calls: int = 5,
        select_registry_route_id: Callable[..., dict | None] | None = None,
    ) -> list[dict]:
        if not cls.looks_like_department_meta_composition(message):
            return []

        department_id = cls.resolve_department_id(message)

        if not department_id:
            return []

        mode = cls.composition_mode(message)
        route_ids = cls.route_ids_for_department(department_id, mode=mode)

        if len(route_ids) < 1:
            return []

        resolve = select_registry_route_id or getattr(
            selection_service,
            "select_registry_route_id",
            None,
        )

        if not callable(resolve):
            return []

        limit = max(1, min(int(max_calls), 12))
        planned: list[dict] = []
        seen_action_ids: set[str] = set()

        for index, route_id in enumerate(route_ids):
            if len(planned) >= limit:
                break

            if not OperationalRouteRegistryService.route_by_id(route_id):
                continue

            selected = resolve(
                route_id,
                message,
                allowed_action_ids=allowed_action_ids or [],
                previous_messages=previous_messages,
            )

            if not isinstance(selected, dict):
                continue

            action_id = str(
                (selected.get("arguments") or {}).get("actionId") or ""
            ).strip()

            if not action_id or action_id in seen_action_ids:
                continue

            seen_action_ids.add(action_id)
            item = dict(selected)
            item["reason"] = cls._reason_for_route(route_id, index=index)
            planned.append(item)

        if mode == "compose" and len(planned) < 2:
            return planned if planned else []

        return planned

    @classmethod
    def _reason_for_route(cls, route_id: str, *, index: int) -> str:
        if index == 0:
            return str(
                ChatAssistantContentService.get(
                    _BUNDLE,
                    "selectionReasons",
                    "primary",
                    default="Consulta o painel de metas e realizado do departamento.",
                )
            )

        if route_id == "dashboardDepartmentIdd":
            return str(
                ChatAssistantContentService.get(
                    _BUNDLE,
                    "selectionReasons",
                    "iddScore",
                    default="Consulta a nota IDD estratégica do departamento.",
                )
            )

        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "selectionReasons",
                "compose",
                default="Complementa a meta departamental com indicador relacionado.",
            )
        )
