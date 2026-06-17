"""Montagem de parâmetros HTTP por estratégia — desacoplada do domínio da rota."""

from __future__ import annotations

import re
from typing import Any, Callable

from app.domain.models.operational_api_route_spec import OperationalApiRouteSpec
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_api_domain_service import (
    ChatOperationalApiDomainService,
)


class OperationalApiParameterBuilderService:
    """Aplica estratégias declaradas em `api_route_domains.json`."""

    def build(
        self,
        spec: OperationalApiRouteSpec,
        action: dict,
        message: str,
        *,
        previous_messages: list | None = None,
        product_builder: Callable[..., dict] | None = None,
    ) -> dict:
        strategy = str(spec.parameter_strategy or "").strip().lower()

        if strategy == "product_code" and product_builder and spec.entity_code:
            return product_builder(
                action,
                spec.entity_code,
                message=message,
            )

        if strategy == "date_branch":
            parameters = self.build_date_branch(
                action,
                message,
                previous_messages=previous_messages,
            )

            if parameters:
                return parameters

            if spec.domain == "supplies_kpi":
                return self.build_supplies_stock(action)

            return parameters

        if strategy == "supplies_stock":
            return self.build_supplies_stock(action)

        return {}

    def build_date_branch(
        self,
        action: dict,
        message: str,
        *,
        previous_messages: list | None = None,
    ) -> dict:
        from app.domain.services.chat_date_range_intent_service import (
            ChatDateRangeIntentService,
        )

        spec = ChatOperationalApiDomainService.parameter_strategy_spec("date_branch")
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        date_range = ChatDateRangeIntentService.resolve(
            message,
            previous_messages=previous_messages,
        )
        patterns = spec.get("patterns") if isinstance(spec.get("patterns"), dict) else {}
        branch_match = re.search(str(patterns.get("branch") or r"\bfilial\s+(\d{2})\b"), normalized)
        branch = branch_match.group(1) if branch_match else None
        context = {
            "branch": branch,
            "branch_match": branch_match,
            "date_range": date_range,
            "normalized": normalized,
        }
        parameters = self._apply_bindings(action, spec, context)

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name or name in parameters:
                continue

            if name.lower() != "granularity" or not parameter.get("required"):
                continue

            parameters[name] = self._infer_granularity(normalized, date_range, spec) or str(
                spec.get("granularityDefault") or "month"
            )

        if not parameters:
            empty_default = spec.get("emptyDefault")

            if isinstance(empty_default, dict):
                parameters = dict(empty_default)

        return parameters

    def build_sale_orders(
        self,
        action: dict,
        message: str,
        *,
        previous_messages: list | None = None,
    ) -> dict:
        spec = ChatOperationalApiDomainService.parameter_strategy_spec("sale_orders")
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        from app.domain.services.chat_date_range_intent_service import (
            ChatDateRangeIntentService,
        )

        date_range = ChatDateRangeIntentService.resolve(
            message,
            previous_messages=previous_messages,
        )
        parameters = self._apply_bindings(
            action,
            spec,
            {
                "normalized": normalized,
                "date_range": date_range,
                "branch": None,
                "branch_match": None,
            },
        )

        if not parameters:
            empty_default = spec.get("emptyDefault")

            if isinstance(empty_default, dict):
                parameters = dict(empty_default)

        if date_range:
            parameters = self.merge_date_range(action, message, parameters, previous_messages=previous_messages)

        return parameters

    def merge_date_range(
        self,
        action: dict,
        message: str,
        parameters: dict,
        *,
        previous_messages: list | None = None,
    ) -> dict:
        from app.domain.services.chat_date_range_intent_service import (
            ChatDateRangeIntentService,
        )

        date_range = ChatDateRangeIntentService.resolve(
            message,
            previous_messages=previous_messages,
        )

        if not date_range:
            return parameters

        spec = ChatOperationalApiDomainService.parameter_strategy_spec("date_branch")
        merged = dict(parameters)
        context = {
            "branch": None,
            "branch_match": None,
            "date_range": date_range,
            "normalized": ChatMessageNormalizationService.normalize_for_matching(message),
        }

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name or name in merged:
                continue

            value = self._resolve_binding_value(
                name,
                spec,
                context,
                allow_sources={
                    "date_range.start",
                    "date_range.end",
                },
            )

            if value is not None:
                merged[name] = value

        return merged

    @classmethod
    def build_supplies_stock(cls, action: dict) -> dict:
        spec = ChatOperationalApiDomainService.parameter_strategy_spec("supplies_stock")

        return cls._apply_bindings(
            action,
            spec,
            {
                "branch": None,
                "branch_match": None,
                "date_range": None,
                "normalized": "",
            },
        )

    @classmethod
    def _apply_bindings(
        cls,
        action: dict,
        spec: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        bindings = spec.get("bindings")

        if not isinstance(bindings, list):
            return {}

        parameters: dict[str, Any] = {}

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name:
                continue

            value = cls._resolve_binding_value(name, spec, context)

            if value is not None:
                parameters[name] = value

        return parameters

    @classmethod
    def _resolve_binding_value(
        cls,
        parameter_name: str,
        spec: dict[str, Any],
        context: dict[str, Any],
        *,
        allow_sources: set[str] | None = None,
    ) -> Any:
        bindings = spec.get("bindings")

        if not isinstance(bindings, list):
            return None

        lowered = str(parameter_name or "").lower()

        for binding in bindings:
            if not isinstance(binding, dict):
                continue

            source = str(binding.get("source") or "").strip()
            aliases = binding.get("matchAliases") or []

            if allow_sources is not None and source not in allow_sources:
                continue

            if not any(str(alias or "").lower() == lowered for alias in aliases):
                continue

            return cls._resolve_source_value(source, binding, spec, context)

        return None

    @classmethod
    def _resolve_source_value(
        cls,
        source: str,
        binding: dict[str, Any],
        spec: dict[str, Any],
        context: dict[str, Any],
    ) -> Any:
        normalized = str(context.get("normalized") or "")
        date_range = context.get("date_range")
        patterns = spec.get("patterns") if isinstance(spec.get("patterns"), dict) else {}

        if source == "branch_regex":
            branch = context.get("branch")

            return branch if branch else None

        if source == "work_center_regex":
            if context.get("branch_match") is not None:
                return None

            pattern = str(patterns.get("work_center") or r"\bct\s+(\S+)")
            match = re.search(pattern, normalized)

            return match.group(1) if match else None

        if source == "product_group_regex":
            pattern = str(patterns.get("product_group") or r"\bgrupo\s+(\d{4})\b")
            match = re.search(pattern, normalized)

            return match.group(1) if match else None

        if source == "date_range.start" and date_range:
            return date_range.start_date

        if source == "date_range.end" and date_range:
            return date_range.end_date

        if source == "pagination.page":
            return 1

        if source == "pagination.page_size":
            return 50

        if source == "granularity_inferred":
            return cls._infer_granularity(normalized, date_range, spec)

        if source == "literal":
            return binding.get("value")

        return None

    @classmethod
    def _infer_granularity(cls, normalized: str, date_range, spec: dict[str, Any]) -> str | None:
        terms = spec.get("granularityTerms")

        if isinstance(terms, dict):
            for granularity, markers in terms.items():
                if not isinstance(markers, list):
                    continue

                if any(str(term) in normalized for term in markers):
                    return str(granularity)

        if date_range:
            return str(spec.get("granularityDefault") or "month")

        return None
