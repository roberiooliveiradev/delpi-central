from __future__ import annotations

from app.application.dto.commercial.commercial_target_request import CommercialTargetRequest
from app.application.dto.commercial.new_clients_average_request import NewClientsAverageRequest
from app.application.dto.commercial.new_clients_rol_pct_request import NewClientsRolPctRequest
from app.application.dto.commercial.sales_conversion_rate_request import SalesConversionRateRequest
from app.application.use_cases.commercial.get_new_clients_average_use_case import (
    GetNewClientsAverageUseCase,
)
from app.application.use_cases.commercial.get_new_clients_rol_pct_use_case import (
    GetNewClientsRolPctUseCase,
)
from app.application.use_cases.commercial.get_rol_target_pct_use_case import (
    GetRolTargetPctUseCase,
)
from app.application.use_cases.commercial.get_sales_conversion_rate_use_case import (
    GetSalesConversionRateUseCase,
)
from app.domain.ports.strategic_indicators.commercial_indicators_snapshot_port import (
    StrategicIndicatorsCommercialIndicatorsSnapshotPort,
)


class CommercialIndicatorsSnapshotProvider(
    StrategicIndicatorsCommercialIndicatorsSnapshotPort,
):
    def __init__(
        self,
        *,
        head_office_rol_target_use_case: GetRolTargetPctUseCase,
        branch_rol_target_use_case: GetRolTargetPctUseCase,
        sales_conversion_rate_use_case: GetSalesConversionRateUseCase,
        new_clients_average_use_case: GetNewClientsAverageUseCase,
        new_clients_rol_pct_use_case: GetNewClientsRolPctUseCase,
    ) -> None:
        self._head_office_rol_target_use_case = head_office_rol_target_use_case
        self._branch_rol_target_use_case = branch_rol_target_use_case
        self._sales_conversion_rate_use_case = sales_conversion_rate_use_case
        self._new_clients_average_use_case = new_clients_average_use_case
        self._new_clients_rol_pct_use_case = new_clients_rol_pct_use_case

    def get_commercial_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        items: list[dict] = []
        errors: list[dict] = []

        self._collect_indicator(
            builder=lambda: self._build_head_office_rol_target_indicator(
                start_date=start_date,
                end_date=end_date,
            ),
            department_id="commercial",
            source="commercial_head_office_rol_target",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_branch_rol_target_indicator(
                start_date=start_date,
                end_date=end_date,
            ),
            department_id="commercial",
            source="commercial_branch_rol_target",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_sales_conversion_rate_indicator(
                start_date=start_date,
                end_date=end_date,
            ),
            department_id="commercial",
            source="commercial_sales_conversion_rate",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_new_clients_average_indicator(
                start_date=start_date,
                end_date=end_date,
            ),
            department_id="commercial",
            source="commercial_new_clients_average",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_new_clients_rol_pct_indicator(
                start_date=start_date,
                end_date=end_date,
            ),
            department_id="commercial",
            source="commercial_new_clients_rol_pct",
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

    def _build_head_office_rol_target_indicator(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        request = CommercialTargetRequest(
            branch="01",
            start_date=start_date,
            end_date=end_date,
        )

        result = self._head_office_rol_target_use_case.execute(request)
        value = self._to_float(result.get("rol_target_pct"))
        goal = 100.0
        gap = round(goal - value, 2) if value is not None else 0.0
        score = self._score_higher_is_better(value=value, goal=goal)

        return {
            "department_id": "commercial",
            "department_name": "Comercial",
            "indicator_id": "commercial-rol-matrix",
            "indicator_name": "ROL Matriz / Meta",
            "weight_pct": 25,
            "goal_2026": "100%",
            "scope_type": "matrix_only",
            "value": value or 0.0,
            "score": score,
            "gap": gap,
            "trend": "up" if value is not None and value >= goal else "stable",
            "classification": self._classify_score(score),
            "source": "commercial_head_office_rol_target",
        }

    def _build_branch_rol_target_indicator(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        request = CommercialTargetRequest(
            branch="02",
            start_date=start_date,
            end_date=end_date,
        )

        result = self._branch_rol_target_use_case.execute(request)
        value = self._to_float(result.get("rol_target_pct"))
        goal = 100.0
        gap = round(goal - value, 2) if value is not None else 0.0
        score = self._score_higher_is_better(value=value, goal=goal)

        return {
            "department_id": "commercial",
            "department_name": "Comercial",
            "indicator_id": "commercial-rol-branch",
            "indicator_name": "ROL Filial / Meta",
            "weight_pct": 25,
            "goal_2026": "100%",
            "scope_type": "branch_only",
            "value": value or 0.0,
            "score": score,
            "gap": gap,
            "trend": "up" if value is not None and value >= goal else "stable",
            "classification": self._classify_score(score),
            "source": "commercial_branch_rol_target",
        }

    def _build_sales_conversion_rate_indicator(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        request = SalesConversionRateRequest(
            branch=None,
            start_date=start_date,
            end_date=end_date,
        )

        result = self._sales_conversion_rate_use_case.execute(request)
        value = self._to_float(result.get("sales_conversion_rate_pct"))
        goal = 30.0
        gap = round(goal - value, 2) if value is not None else 0.0
        score = self._score_higher_is_better(value=value, goal=goal)

        return {
            "department_id": "commercial",
            "department_name": "Comercial",
            "indicator_id": "commercial-closing-rate",
            "indicator_name": "Taxa de Fechamento de Negócios",
            "weight_pct": 20,
            "goal_2026": "30%",
            "scope_type": "consolidated",
            "value": value or 0.0,
            "score": score,
            "gap": gap,
            "trend": "up" if value is not None and value >= goal else "stable",
            "classification": self._classify_score(score),
            "source": "commercial_sales_conversion_rate",
        }

    def _build_new_clients_average_indicator(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        request = NewClientsAverageRequest(
            branch=None,
            start_date=start_date,
            end_date=end_date,
        )

        result = self._new_clients_average_use_case.execute(request)
        value = self._to_float(result.get("monthly_average"))
        goal = 10.0
        gap = round(goal - value, 2) if value is not None else 0.0
        score = self._score_higher_is_better(value=value, goal=goal)

        return {
            "department_id": "commercial",
            "department_name": "Comercial",
            "indicator_id": "commercial-new-clients",
            "indicator_name": "Número de Novos Clientes (média mensal)",
            "weight_pct": 15,
            "goal_2026": "10 novos/mês",
            "scope_type": "consolidated",
            "value": value or 0.0,
            "score": score,
            "gap": gap,
            "trend": "up" if value is not None and value >= goal else "stable",
            "classification": self._classify_score(score),
            "source": "commercial_new_clients_average",
        }

    def _build_new_clients_rol_pct_indicator(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        request = NewClientsRolPctRequest(
            branch=None,
            start_date=start_date,
            end_date=end_date,
        )

        result = self._new_clients_rol_pct_use_case.execute(request)
        value = self._to_float(result.get("new_clients_rol_pct"))
        goal = 12.0
        gap = round(goal - value, 2) if value is not None else 0.0
        score = self._score_higher_is_better(value=value, goal=goal)

        return {
            "department_id": "commercial",
            "department_name": "Comercial",
            "indicator_id": "commercial-new-rol",
            "indicator_name": "% ROL de Novos Clientes",
            "weight_pct": 15,
            "goal_2026": "12%",
            "scope_type": "consolidated",
            "value": value or 0.0,
            "score": score,
            "gap": gap,
            "trend": "up" if value is not None and value >= goal else "stable",
            "classification": self._classify_score(score),
            "source": "commercial_new_clients_rol_pct",
        }

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