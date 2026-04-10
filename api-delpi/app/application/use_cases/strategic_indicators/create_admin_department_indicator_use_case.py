from __future__ import annotations

from app.domain.ports.strategic_indicators.department_indicators_repository_port import (
    StrategicIndicatorsDepartmentIndicatorsRepositoryPort,
)


class CreateStrategicIndicatorsAdminDepartmentIndicatorUseCase:
    VALID_SCOPE_TYPES = {"consolidated", "per_unit"}

    def __init__(
        self,
        repository: StrategicIndicatorsDepartmentIndicatorsRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        department_id: str,
        body: dict,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        if not department_id.strip():
            raise ValueError("department_id é obrigatório.")

        indicator_id = (body.get("indicator_id") or "").strip()
        indicator_name = (body.get("indicator_name") or "").strip()
        scope_type = (body.get("scope_type") or "").strip()

        if not indicator_id:
            raise ValueError("indicator_id é obrigatório.")
        if not indicator_name:
            raise ValueError("indicator_name é obrigatório.")
        if scope_type not in self.VALID_SCOPE_TYPES:
            raise ValueError("scope_type inválido.")

        weight_pct = float(body.get("weight_pct") or 0)
        if weight_pct < 0 or weight_pct > 100:
            raise ValueError("weight_pct deve estar entre 0 e 100.")

        return self._repository.create_department_indicator(
            department_id=department_id.strip(),
            indicator_id=indicator_id,
            indicator_name=indicator_name,
            weight_pct=weight_pct,
            scope_type=scope_type,
            strategic_description=(body.get("strategic_description") or "").strip(),
            source_key=(body.get("source_key") or None),
            display_order=int(body.get("display_order") or 0),
            actor_user_id=actor_user_id,
            actor_email=actor_email,
        )