"""Classificação de domínios de rota operacional — vocabulário em api_route_domains.json."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


def invalidate_operational_api_domain_cache() -> None:
    _api_route_domains_content.cache_clear()


@lru_cache(maxsize=1)
def _api_route_domains_content() -> dict[str, Any]:
    return ChatAssistantContentService.load_bundle("api_route_domains")


class ChatOperationalApiDomainService:
    """Resolve domínio e estratégia de parâmetros a partir do path ou da spec."""

    @classmethod
    def domains(cls) -> dict[str, dict[str, Any]]:
        return dict((_api_route_domains_content().get("domains") or {}))

    @classmethod
    def classify_path(cls, path: str) -> str:
        lowered = str(path or "").lower().strip()

        if not lowered:
            return "generic"

        for domain_id, config in cls._ordered_domains():
            markers = config.get("pathMarkers") or []

            if not markers:
                continue

            excludes = config.get("excludePathMarkers") or []

            if any(marker in lowered for marker in excludes):
                continue

            if any(marker in lowered for marker in markers):
                return str(domain_id)

        return "generic"

    @classmethod
    def parameter_strategy_for_domain(cls, domain: str) -> str:
        config = cls.domains().get(str(domain or "").strip())

        if not isinstance(config, dict):
            return "semantic"

        strategy = config.get("parameterStrategy")

        return str(strategy).strip() if isinstance(strategy, str) and strategy.strip() else "semantic"

    @classmethod
    def parameter_strategy_ids(cls) -> frozenset[str]:
        strategies = _api_route_domains_content().get("parameterStrategies") or {}

        if not isinstance(strategies, dict):
            return frozenset()

        return frozenset(
            str(strategy_id).strip()
            for strategy_id in strategies
            if str(strategy_id).strip()
        )

    @classmethod
    def parameter_strategy_spec(cls, strategy_id: str) -> dict[str, Any]:
        strategies = _api_route_domains_content().get("parameterStrategies") or {}

        if not isinstance(strategies, dict):
            return {}

        node = strategies.get(str(strategy_id or "").strip())

        if isinstance(node, dict):
            return dict(node)

        if isinstance(node, str) and node.strip():
            return {"description": node.strip()}

        return {}

    @classmethod
    def method_for_domain(cls, domain: str) -> str:
        config = cls.domains().get(str(domain or "").strip())

        if not isinstance(config, dict):
            return "GET"

        method = config.get("method")

        return str(method).strip().upper() if isinstance(method, str) and method.strip() else "GET"

    @classmethod
    def domain_label(cls, domain: str) -> str:
        config = cls.domains().get(str(domain or "").strip())

        if not isinstance(config, dict):
            return str(domain or "generic")

        label = config.get("label")

        return str(label).strip() if isinstance(label, str) and label.strip() else str(domain)

    @classmethod
    def _ordered_domains(cls) -> list[tuple[str, dict[str, Any]]]:
        configured = cls.domains()
        priority = (
            "product_search",
            "product",
            "product_exclusive_catalog",
            "production_consumption",
            "production_losses",
            "production_schedule",
            "production_orders",
            "production_work_centers",
            "purchases_ranking",
            "department_kpi",
            "supplies_kpi",
            "lmp",
            "sql",
            "system",
            "generic",
        )
        ordered: list[tuple[str, dict[str, Any]]] = []

        for domain_id in priority:
            config = configured.get(domain_id)

            if isinstance(config, dict):
                ordered.append((domain_id, config))

        for domain_id, config in configured.items():
            if domain_id not in priority and isinstance(config, dict):
                ordered.append((domain_id, config))

        return ordered
