"""E1.S5 — parameterStrategy: shadow e cutover parcial para binder OpenAPI."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_CUTOVER_STRATEGIES = frozenset({"none", "semantic", "sale_orders"})


class ParameterStrategyShadowObservabilityService:
    @classmethod
    def record(cls, shadow: dict[str, Any] | None) -> None:
        if not isinstance(shadow, dict):
            return
        logger.info(
            "parameter_strategy_shadow",
            extra={
                "metric": "parameter_strategy_shadow",
                "strategy": str(shadow.get("strategy") or ""),
                "authority": str(shadow.get("authority") or ""),
                "agree": bool(shadow.get("agree")),
                "agreeExact": bool(shadow.get("agreeExact")),
                "agreeCompatible": bool(shadow.get("agreeCompatible")),
                "legacyKeyCount": int(shadow.get("legacyKeyCount") or 0),
                "candidateKeyCount": int(shadow.get("candidateKeyCount") or 0),
                "error": str(shadow.get("error") or "") or None,
            },
        )


class ParameterStrategyShadowService:
    """Shadow + cutover parcial (`none`/`semantic`/`sale_orders`) → `_bind_arguments`.

    Cutover on: authority = OpenAPI binder; observer = strategy legada.
    Cutover off: authority = strategy; observer = binder (comportamento E1.S5 shadow).
    """

    @classmethod
    def cutover_strategies(cls) -> frozenset[str]:
        return _CUTOVER_STRATEGIES

    @classmethod
    def shadowable_strategies(cls) -> frozenset[str]:
        return _CUTOVER_STRATEGIES

    @classmethod
    def cutover_enabled(cls) -> bool:
        from app.domain.services.openapi_tool_routing_content_service import (
            OpenApiToolRoutingContentService,
        )

        return OpenApiToolRoutingContentService.bool_setting(
            "parameterStrategyShadow",
            "cutoverEnabled",
            default=False,
        )

    @classmethod
    def shadow_enabled(cls) -> bool:
        from app.domain.services.openapi_tool_routing_content_service import (
            OpenApiToolRoutingContentService,
        )

        return OpenApiToolRoutingContentService.bool_setting(
            "parameterStrategyShadow",
            "enabled",
            default=False,
        )

    @classmethod
    def uses_openapi_authority(cls, strategy: str) -> bool:
        return str(strategy or "").strip() in _CUTOVER_STRATEGIES and cls.cutover_enabled()

    @classmethod
    def bind_via_openapi(
        cls,
        action: dict[str, Any],
        message: str,
        *,
        previous_messages: list | None = None,
    ) -> dict[str, Any]:
        from app.application.services.plan_external_actions_service import (
            PlanExternalActionsService,
        )

        parameters, _body, _missing = PlanExternalActionsService._bind_arguments(
            message,
            action,
            context_parameters={},
            previous_messages=previous_messages,
        )
        return dict(parameters) if isinstance(parameters, dict) else {}

    @classmethod
    def legacy_strategy_parameters(
        cls,
        *,
        strategy: str,
        action: dict[str, Any],
        message: str,
        previous_messages: list | None = None,
    ) -> dict[str, Any]:
        name = str(strategy or "").strip()
        if name in {"none", "semantic"}:
            return {}
        if name == "sale_orders":
            from app.domain.services.operational_api_parameter_builder_service import (
                OperationalApiParameterBuilderService,
            )

            return OperationalApiParameterBuilderService().build_sale_orders(
                action,
                message,
                previous_messages=previous_messages,
            )
        return {}

    @classmethod
    def compare(
        cls,
        *,
        strategy: str,
        legacy_parameters: dict[str, Any] | None,
        action: dict[str, Any],
        message: str,
        previous_messages: list | None = None,
    ) -> dict[str, Any] | None:
        strategy_name = str(strategy or "").strip()
        if strategy_name not in _CUTOVER_STRATEGIES:
            return None
        if not cls.shadow_enabled():
            return None

        try:
            binder_params = cls.bind_via_openapi(
                action,
                message,
                previous_messages=previous_messages,
            )
            strategy_params = cls.legacy_strategy_parameters(
                strategy=strategy_name,
                action=action,
                message=message,
                previous_messages=previous_messages,
            )
        except Exception:
            shadow = {
                "strategy": strategy_name,
                "authority": "error",
                "legacyParameters": cls._normalize_params(legacy_parameters),
                "candidateParameters": {},
                "agree": False,
                "agreeExact": False,
                "agreeCompatible": False,
                "legacyKeyCount": 0,
                "candidateKeyCount": 0,
                "error": "bind_failed",
            }
            ParameterStrategyShadowObservabilityService.record(shadow)
            return shadow

        cutover = cls.cutover_enabled()
        if cutover:
            # Authority = binder; observer = strategy legada.
            authority_params = binder_params
            observer_params = strategy_params
            authority = "openapi_binder"
        else:
            # Shadow-only: authority = strategy (já aplicada); observer = binder.
            authority_params = legacy_parameters if legacy_parameters is not None else strategy_params
            observer_params = binder_params
            authority = "strategy"

        authority_n = cls._normalize_params(authority_params)
        observer_n = cls._normalize_params(observer_params)
        agree_exact = authority_n == observer_n
        agree_compatible = all(
            observer_n.get(key) == value for key, value in authority_n.items()
        )
        if strategy_name in {"none", "semantic"}:
            agree = agree_exact
        else:
            agree = agree_compatible if cutover else agree_compatible

        shadow = {
            "strategy": strategy_name,
            "authority": authority,
            "cutover": cutover,
            "legacyParameters": observer_n if cutover else authority_n,
            "candidateParameters": authority_n if cutover else observer_n,
            "agree": agree,
            "agreeExact": agree_exact,
            "agreeCompatible": agree_compatible,
            "legacyKeyCount": len(observer_n if cutover else authority_n),
            "candidateKeyCount": len(authority_n if cutover else observer_n),
        }
        ParameterStrategyShadowObservabilityService.record(shadow)
        return shadow

    @staticmethod
    def _normalize_params(parameters: dict[str, Any] | None) -> dict[str, str]:
        normalized: dict[str, str] = {}
        if not isinstance(parameters, dict):
            return normalized
        for key, value in parameters.items():
            name = str(key or "").strip()
            if not name or value is None:
                continue
            text = str(value).strip()
            if not text:
                continue
            normalized[name] = text
        return normalized
