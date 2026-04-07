from __future__ import annotations

from app.application.dto.financial.get_rol_request import GetRolRequest
from app.application.dto.production.production_request import ProductionRequest
from app.application.use_cases.production.get_depreciation_pct_use_case import (
    GetDepreciationPctUseCase,
)
from app.application.use_cases.production.get_direct_labor_cost_pct_use_case import (
    GetDirectLaborCostPctUseCase,
)
from app.application.use_cases.production.get_on_time_delivery_pct_use_case import (
    GetOnTimeDeliveryPctUseCase,
)
from app.application.use_cases.production.get_overall_equipment_effectiveness_pct_use_case import (
    GetOverallEquipmentEffectivenessPctUseCase,
)
from app.application.use_cases.production.get_production_cost_pct_use_case import (
    GetProductionCostPctUseCase,
)
from app.domain.ports.strategic_indicators.production_indicators_snapshot_port import (
    StrategicIndicatorsProductionIndicatorsSnapshotPort,
)


class ProductionIndicatorsSnapshotProvider(
    StrategicIndicatorsProductionIndicatorsSnapshotPort,
):
    def __init__(
        self,
        *,
        direct_labor_use_case: GetDirectLaborCostPctUseCase,
        production_cost_use_case: GetProductionCostPctUseCase,
        depreciation_use_case: GetDepreciationPctUseCase,
        oee_use_case: GetOverallEquipmentEffectivenessPctUseCase,
        otd_use_case: GetOnTimeDeliveryPctUseCase,
    ) -> None:
        self._direct_labor_use_case = direct_labor_use_case
        self._production_cost_use_case = production_cost_use_case
        self._depreciation_use_case = depreciation_use_case
        self._oee_use_case = oee_use_case
        self._otd_use_case = otd_use_case

    def get_production_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        items: list[dict] = []
        errors: list[dict] = []

        matrix_request = self._build_production_request(
            branch="01",
            start_date=start_date,
            end_date=end_date,
        )
        branch_request = self._build_production_request(
            branch="02",
            start_date=start_date,
            end_date=end_date,
        )

        matrix_rol_request = self._build_rol_request(
            branch="01",
            start_date=start_date,
            end_date=end_date,
        )
        branch_rol_request = self._build_rol_request(
            branch="02",
            start_date=start_date,
            end_date=end_date,
        )

        self._collect_indicator(
            builder=lambda: self._build_direct_labor_indicator(
                matrix_request=matrix_request,
                branch_request=branch_request,
                matrix_rol_request=matrix_rol_request,
                branch_rol_request=branch_rol_request,
            ),
            department_id="production",
            source="production_direct_labor",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_production_cost_indicator(
                matrix_request=matrix_request,
                branch_request=branch_request,
                matrix_rol_request=matrix_rol_request,
                branch_rol_request=branch_rol_request,
            ),
            department_id="production",
            source="production_cost",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_depreciation_indicator(
                matrix_request=matrix_request,
                branch_request=branch_request,
                matrix_rol_request=matrix_rol_request,
                branch_rol_request=branch_rol_request,
            ),
            department_id="production",
            source="production_depreciation",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_oee_indicator(
                matrix_request=matrix_request,
                branch_request=branch_request,
            ),
            department_id="production",
            source="production_oee",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_otd_indicator(
                matrix_request=matrix_request,
                branch_request=branch_request,
            ),
            department_id="production",
            source="production_otd",
            items=items,
            errors=errors,
        )

        return {
            "items": items,
            "errors": errors,
        }

    def _collect_indicator(
        self,
        *,
        builder,
        department_id: str,
        source: str,
        items: list[dict],
        errors: list[dict],
    ) -> None:
        try:
            items.append(builder())
        except Exception as exc:
            errors.append(
                {
                    "department_id": department_id,
                    "source": source,
                    "message": str(exc),
                }
            )

    def _build_direct_labor_indicator(
        self,
        *,
        matrix_request: ProductionRequest,
        branch_request: ProductionRequest,
        matrix_rol_request: GetRolRequest,
        branch_rol_request: GetRolRequest,
    ) -> dict:
        matrix_result = self._direct_labor_use_case.execute(
            matrix_request,
            matrix_rol_request,
        )
        branch_result = self._direct_labor_use_case.execute(
            branch_request,
            branch_rol_request,
        )

        matrix_value = self._to_float(matrix_result.get("direct_labor_cost_pct"))
        branch_value = self._to_float(branch_result.get("direct_labor_cost_pct"))
        value = self._average_values(matrix_value, branch_value)

        goal = 10.0
        gap = round(value - goal, 2) if value is not None else 0.0
        score = self._score_lower_is_better(value=value, goal=goal)

        return {
            "department_id": "production",
            "department_name": "Produção",
            "indicator_id": "production-direct-labor",
            "indicator_name": "Custo Mão de Obra Direta / ROL",
            "weight_pct": 25,
            "goal_2026": "10,0%",
            "scope_type": "per_unit",
            "value": value or 0.0,
            "score": score,
            "gap": gap,
            "trend": "up" if value is not None and value <= goal else "stable",
            "classification": self._classify_score(score),
            "source": "production_direct_labor",
        }

    def _build_production_cost_indicator(
        self,
        *,
        matrix_request: ProductionRequest,
        branch_request: ProductionRequest,
        matrix_rol_request: GetRolRequest,
        branch_rol_request: GetRolRequest,
    ) -> dict:
        matrix_result = self._production_cost_use_case.execute(
            matrix_request,
            matrix_rol_request,
        )
        branch_result = self._production_cost_use_case.execute(
            branch_request,
            branch_rol_request,
        )

        matrix_value = self._to_float(matrix_result.get("production_cost_pct"))
        branch_value = self._to_float(branch_result.get("production_cost_pct"))
        value = self._average_values(matrix_value, branch_value)

        goal = 32.0
        gap = round(value - goal, 2) if value is not None else 0.0
        score = self._score_lower_is_better(value=value, goal=goal)

        return {
            "department_id": "production",
            "department_name": "Produção",
            "indicator_id": "production-costs",
            "indicator_name": "Custos de Produção / ROL",
            "weight_pct": 20,
            "goal_2026": "32,0%",
            "scope_type": "per_unit",
            "value": value or 0.0,
            "score": score,
            "gap": gap,
            "trend": "up" if value is not None and value <= goal else "stable",
            "classification": self._classify_score(score),
            "source": "production_cost",
        }

    def _build_depreciation_indicator(
        self,
        *,
        matrix_request: ProductionRequest,
        branch_request: ProductionRequest,
        matrix_rol_request: GetRolRequest,
        branch_rol_request: GetRolRequest,
    ) -> dict:
        matrix_result = self._depreciation_use_case.execute(
            matrix_request,
            matrix_rol_request,
        )
        branch_result = self._depreciation_use_case.execute(
            branch_request,
            branch_rol_request,
        )

        matrix_value = self._to_float(matrix_result.get("depreciation_pct"))
        branch_value = self._to_float(branch_result.get("depreciation_pct"))
        value = self._average_values(matrix_value, branch_value)

        goal = 1.5
        gap = round(value - goal, 2) if value is not None else 0.0
        score = self._score_lower_is_better(value=value, goal=goal)

        return {
            "department_id": "production",
            "department_name": "Produção",
            "indicator_id": "production-depreciation",
            "indicator_name": "Depreciação / ROL",
            "weight_pct": 10,
            "goal_2026": "1,5%",
            "scope_type": "per_unit",
            "value": value or 0.0,
            "score": score,
            "gap": gap,
            "trend": "up" if value is not None and value <= goal else "stable",
            "classification": self._classify_score(score),
            "source": "production_depreciation",
        }

    def _build_oee_indicator(
        self,
        *,
        matrix_request: ProductionRequest,
        branch_request: ProductionRequest,
    ) -> dict:
        matrix_result = self._oee_use_case.execute(matrix_request)
        branch_result = self._oee_use_case.execute(branch_request)

        matrix_value = self._to_float(
            matrix_result.get("overall_equipment_effectiveness_pct")
        )
        branch_value = self._to_float(
            branch_result.get("overall_equipment_effectiveness_pct")
        )
        value = self._average_values(matrix_value, branch_value)

        goal = 70.0
        gap = round(goal - value, 2) if value is not None else 0.0
        score = self._score_higher_is_better(value=value, goal=goal)

        return {
            "department_id": "production",
            "department_name": "Produção",
            "indicator_id": "production-oee",
            "indicator_name": "OEE (Eficiência Global dos Equip.)",
            "weight_pct": 20,
            "goal_2026": "70%",
            "scope_type": "per_unit",
            "value": value or 0.0,
            "score": score,
            "gap": gap,
            "trend": "up" if value is not None and value >= goal else "stable",
            "classification": self._classify_score(score),
            "source": "production_oee",
        }

    def _build_otd_indicator(
        self,
        *,
        matrix_request: ProductionRequest,
        branch_request: ProductionRequest,
    ) -> dict:
        matrix_result = self._otd_use_case.execute(matrix_request)
        branch_result = self._otd_use_case.execute(branch_request)

        matrix_value = self._to_float(matrix_result.get("on_time_delivery_pct"))
        branch_value = self._to_float(branch_result.get("on_time_delivery_pct"))
        value = self._average_values(matrix_value, branch_value)

        goal = 92.0
        gap = round(goal - value, 2) if value is not None else 0.0
        score = self._score_higher_is_better(value=value, goal=goal)

        return {
            "department_id": "production",
            "department_name": "Produção",
            "indicator_id": "production-otd",
            "indicator_name": "OTD (Entrega no Prazo)",
            "weight_pct": 25,
            "goal_2026": "92%",
            "scope_type": "per_unit",
            "value": value or 0.0,
            "score": score,
            "gap": gap,
            "trend": "up" if value is not None and value >= goal else "stable",
            "classification": self._classify_score(score),
            "source": "production_otd",
        }

    def _build_production_request(
        self,
        *,
        branch: str,
        start_date: str | None,
        end_date: str | None,
    ) -> ProductionRequest:
        return ProductionRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

    def _build_rol_request(
        self,
        *,
        branch: str,
        start_date: str | None,
        end_date: str | None,
    ) -> GetRolRequest:
        return GetRolRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

    def _average_values(
        self,
        first: float | None,
        second: float | None,
    ) -> float | None:
        valid = [value for value in [first, second] if value is not None]
        if not valid:
            return None
        return round(sum(valid) / len(valid), 2)

    def _to_float(self, value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _score_higher_is_better(self, *, value: float | None, goal: float) -> float:
        if value is None or goal <= 0:
            return 0.0

        ratio = value / goal
        score = ratio * 10
        return round(min(score, 10.0), 2)

    def _score_lower_is_better(self, *, value: float | None, goal: float) -> float:
        if value is None or goal <= 0:
            return 0.0

        ratio = goal / value if value > 0 else 10.0
        score = ratio * 10
        return round(min(score, 10.0), 2)

    def _classify_score(self, score: float) -> str:
        if score >= 9:
            return "Excelência Integrada"
        if score >= 8:
            return "Alto Desempenho"
        if score >= 7:
            return "Satisfatório com Alertas"
        if score >= 6:
            return "Regular, Exige Ação"
        return "Crítico"