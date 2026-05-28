from __future__ import annotations

from si_app.application.services.strategic_indicators.indicator_source_key_validation import (
    normalize_indicator_source_key,
    validate_indicator_source_key,
)
from si_app.domain.ports.strategic_indicators.department_indicators_repository_port import (
    StrategicIndicatorsDepartmentIndicatorsRepositoryPort,
)


class UpdateStrategicIndicatorsAdminDepartmentIndicatorUseCase:
    VALID_SCOPE_TYPES = {"consolidated", "per_unit"}
    VALID_PERFORMANCE_DIRECTIONS = {
        "higher_is_better",
        "lower_is_better",
    }

    def __init__(
        self,
        repository: StrategicIndicatorsDepartmentIndicatorsRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        indicator_id: str,
        body: dict,
        actor_user_id: str | None,
    ) -> dict:
        if not indicator_id.strip():
            raise ValueError("indicator_id é obrigatório.")

        indicator_name = (body.get("indicator_name") or "").strip()
        scope_type = (body.get("scope_type") or "").strip()
        performance_direction = (
            body.get("performance_direction") or "higher_is_better"
        ).strip()

        if not indicator_name:
            raise ValueError("indicator_name é obrigatório.")
        if scope_type not in self.VALID_SCOPE_TYPES:
            raise ValueError("scope_type inválido.")
        if performance_direction not in self.VALID_PERFORMANCE_DIRECTIONS:
            raise ValueError("performance_direction inválido.")

        weight_pct = float(body.get("weight_pct") or 0)
        if weight_pct < 0 or weight_pct > 100:
            raise ValueError("weight_pct deve estar entre 0 e 100.")

        value_decimals = int(body.get("value_decimals") if body.get("value_decimals") is not None else 2)
        if value_decimals < 0 or value_decimals > 6:
            raise ValueError("value_decimals deve estar entre 0 e 6.")

        new_indicator_id = (body.get("new_indicator_id") or "").strip() or None
        is_active = bool(body.get("is_active", True))
        source_key = normalize_indicator_source_key(body.get("source_key"))
        validate_indicator_source_key(source_key, is_active=is_active)

        return self._repository.update_department_indicator(
            indicator_id=indicator_id.strip(),
            new_indicator_id=new_indicator_id,
            indicator_name=indicator_name,
            weight_pct=weight_pct,
            scope_type=scope_type,
            performance_direction=performance_direction,
            strategic_description=(body.get("strategic_description") or "").strip(),
            source_key=source_key,
            value_unit=(body.get("value_unit") or None),
            value_prefix=(body.get("value_prefix") or None),
            value_suffix=(body.get("value_suffix") or None),
            value_decimals=value_decimals,
            is_active=is_active,
            display_order=int(body.get("display_order") or 0),
            actor_user_id=actor_user_id,
        )