from __future__ import annotations

from si_app.domain.ports.strategic_indicators.admin_departments_repository_port import (
    StrategicIndicatorsAdminDepartmentsRepositoryPort,
)


class UpdateStrategicIndicatorsAdminDepartmentUseCase:
    VALID_AGGREGATION_MODES = {"consolidated", "average_of_units"}

    def __init__(
        self,
        repository: StrategicIndicatorsAdminDepartmentsRepositoryPort,
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

        department_name = (body.get("department_name") or "").strip()
        short_name = (body.get("short_name") or "").strip()
        strategic_summary = (body.get("strategic_summary") or "").strip()
        headline_goal = (body.get("headline_goal") or "").strip()
        supporting_focus = (body.get("supporting_focus") or "").strip()
        aggregation_mode = (body.get("aggregation_mode") or "").strip()

        if not department_name:
            raise ValueError("department_name é obrigatório.")
        if not short_name:
            raise ValueError("short_name é obrigatório.")
        if aggregation_mode not in self.VALID_AGGREGATION_MODES:
            raise ValueError("aggregation_mode inválido.")

        weight_pct = float(body.get("weight_pct") or 0)
        if weight_pct < 0 or weight_pct > 100:
            raise ValueError("weight_pct deve estar entre 0 e 100.")

        return self._repository.update_department(
            department_id=department_id.strip(),
            department_name=department_name,
            short_name=short_name,
            strategic_summary=strategic_summary,
            headline_goal=headline_goal,
            supporting_focus=supporting_focus,
            weight_pct=weight_pct,
            aggregation_mode=aggregation_mode,
            is_active=bool(body.get("is_active", True)),
            display_order=int(body.get("display_order") or 0),
            actor_user_id=actor_user_id,
            actor_email=actor_email,
        )