"""E1.S5 — shadow parameterStrategy residual vs OpenAPI binder genérico."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_SHADOWABLE = frozenset({"none", "semantic", "sale_orders"})


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
                "agree": bool(shadow.get("agree")),
                "agreeExact": bool(shadow.get("agreeExact")),
                "agreeCompatible": bool(shadow.get("agreeCompatible")),
                "legacyKeyCount": int(shadow.get("legacyKeyCount") or 0),
                "candidateKeyCount": int(shadow.get("candidateKeyCount") or 0),
                "error": str(shadow.get("error") or "") or None,
            },
        )


class ParameterStrategyShadowService:
    """Compara params do resolver (strategy) com PlanExternalActionsService._bind_arguments.

    Não altera o binding authority. Lexical/deterministic only — sem LLM.
    """

    @classmethod
    def shadowable_strategies(cls) -> frozenset[str]:
        return _SHADOWABLE

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
        from app.domain.services.openapi_tool_routing_content_service import (
            OpenApiToolRoutingContentService,
        )

        strategy_name = str(strategy or "").strip()
        if strategy_name not in _SHADOWABLE:
            return None
        if not OpenApiToolRoutingContentService.bool_setting(
            "parameterStrategyShadow",
            "enabled",
            default=False,
        ):
            return None

        legacy = cls._normalize_params(legacy_parameters)
        try:
            from app.application.services.plan_external_actions_service import (
                PlanExternalActionsService,
            )

            candidate_raw, _body, _missing = PlanExternalActionsService._bind_arguments(
                message,
                action,
                context_parameters={},
                previous_messages=previous_messages,
            )
            candidate = cls._normalize_params(candidate_raw)
        except Exception:
            shadow = {
                "strategy": strategy_name,
                "legacyParameters": legacy,
                "candidateParameters": {},
                "agree": False,
                "agreeExact": False,
                "agreeCompatible": False,
                "legacyKeyCount": len(legacy),
                "candidateKeyCount": 0,
                "error": "bind_failed",
            }
            ParameterStrategyShadowObservabilityService.record(shadow)
            return shadow

        agree_exact = legacy == candidate
        agree_compatible = all(candidate.get(key) == value for key, value in legacy.items())
        # none/semantic: legacy empty — exact match is the meaningful signal.
        # sale_orders: compatible (candidate may add schema-grounded extras).
        if strategy_name in {"none", "semantic"}:
            agree = agree_exact
        else:
            agree = agree_compatible

        shadow = {
            "strategy": strategy_name,
            "legacyParameters": legacy,
            "candidateParameters": candidate,
            "agree": agree,
            "agreeExact": agree_exact,
            "agreeCompatible": agree_compatible,
            "legacyKeyCount": len(legacy),
            "candidateKeyCount": len(candidate),
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
