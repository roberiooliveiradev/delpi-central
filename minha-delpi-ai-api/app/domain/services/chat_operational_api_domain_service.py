"""Classificação de domínios de rota operacional — labels/methods em api_route_domains.json.

Domain id inference: ``ApiRouteDomainInferenceService`` from Action Catalog /
OpenAPI semantic metadata (explicit apiRouteDomain, entity, category).
Path fragments are not authority (E11.S2).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.api_route_domain_inference_service import (
    ApiRouteDomainInferenceService,
)
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


def invalidate_operational_api_domain_cache() -> None:
    _api_route_domains_content.cache_clear()


@lru_cache(maxsize=1)
def _api_route_domains_content() -> dict[str, Any]:
    return ChatAssistantContentService.load_bundle("api_route_domains")


class ChatOperationalApiDomainService:
    """Resolve domínio e estratégia de parâmetros a partir de metadata semântica."""

    @classmethod
    def domains(cls) -> dict[str, dict[str, Any]]:
        return dict((_api_route_domains_content().get("domains") or {}))

    @classmethod
    def known_domain_ids(cls) -> frozenset[str]:
        return frozenset(str(key).strip() for key in cls.domains() if str(key).strip())

    @classmethod
    def category_to_domain(cls) -> dict[str, str]:
        bindings = _api_route_domains_content().get("semanticBindings") or {}
        raw = bindings.get("categoryToDomain") if isinstance(bindings, dict) else {}
        if not isinstance(raw, dict):
            return {}
        return {
            str(key).strip().lower(): str(value).strip().lower()
            for key, value in raw.items()
            if str(key).strip() and str(value).strip()
        }

    @classmethod
    def entity_to_domain(cls) -> dict[str, str]:
        bindings = _api_route_domains_content().get("semanticBindings") or {}
        raw = bindings.get("entityToDomain") if isinstance(bindings, dict) else {}
        if not isinstance(raw, dict):
            return {}
        return {
            str(key).strip().lower(): str(value).strip().lower()
            for key, value in raw.items()
            if str(key).strip() and str(value).strip()
        }

    @classmethod
    def classify_action(cls, action: dict[str, Any] | None) -> str:
        return ApiRouteDomainInferenceService.infer_from_action(
            action,
            known_domain_ids=cls.known_domain_ids(),
            category_to_domain=cls.category_to_domain(),
            entity_to_domain=cls.entity_to_domain(),
        )

    @classmethod
    def classify_path(cls, path: str) -> str:
        """Deprecated stub: path is not domain authority (always generic)."""
        return ApiRouteDomainInferenceService.infer_from_path(path)

    @classmethod
    def parameter_strategy_for_domain(cls, domain: str) -> str:
        """Legacy domain→strategy map; prefer ParameterStrategyInferenceService for actions."""
        config = cls.domains().get(str(domain or "").strip())

        if not isinstance(config, dict):
            return "semantic"

        strategy = config.get("parameterStrategy")

        return str(strategy).strip() if isinstance(strategy, str) and strategy.strip() else "semantic"

    @classmethod
    def parameter_strategy_for_path(cls, path: str) -> str:
        from app.domain.services.parameter_strategy_inference_service import (
            ParameterStrategyInferenceService,
        )

        return ParameterStrategyInferenceService.infer_from_path(path)

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
