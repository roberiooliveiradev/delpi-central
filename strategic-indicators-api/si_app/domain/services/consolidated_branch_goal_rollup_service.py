"""Rollup canônico de metas por filial → visão consolidada (01+02).

Curva mensal: mescla os pontos das filiais em uma curva consolidada
(goal_mode=monthly_curve) para o serialize aplicar o prorata canônico —
meses completos preservam o valor cadastrado e só competências incompletas
são proporcionalizadas. Metas standard seguem agregadas pelo goal_value.
"""

from __future__ import annotations

from typing import Any, Protocol

from si_app.application.services.strategic_indicators.goal_value_policy import (
    expected_monthly_curve_points,
)
from si_app.shared.consolidated_value_aggregation import (
    aggregate_branch_goal_values,
    is_source_consolidated_mode,
    normalize_branch_value_aggregation,
)
from si_app.shared.goal_scope import BRANCH_UNIT_CODES

_FLAT_CURVE_PERIODICITIES = frozenset({"monthly", "quarterly", "annual", "weekly"})


class _ReferenceGoalResolver(Protocol):
    def resolve_reference_goal(
        self,
        *,
        goal_value: float | None,
        goal_periodicity: str,
        goal_mode: str,
        monthly_targets: list,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> float | None: ...


class ConsolidatedBranchGoalRollupService:
    """Agrega metas das filiais 01/02 para a visão consolidada do SI."""

    def __init__(self, *, reference_resolver: _ReferenceGoalResolver) -> None:
        self._reference_resolver = reference_resolver

    def rollup_branch_goals(
        self,
        *,
        indicator: dict[str, Any],
        branch_goals_by_code: dict[str, dict],
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> dict | None:
        """
        Retorna goal dict pronto para serialize (goal_value + mode), ou None.

        - currency/count (sum): soma referências ou goal_value
        - percent/ppm (average): média
        - monthly_curve: mescla pontos das filiais → monthly_curve consolidada
          (prorata canônico no serialize); fallback legado se não mesclável
        """
        branch_value_aggregation = indicator.get("branch_value_aggregation")
        if is_source_consolidated_mode(branch_value_aggregation):
            return None

        branch_goals = [
            branch_goals_by_code[code]
            for code in BRANCH_UNIT_CODES
            if branch_goals_by_code.get(code)
            and branch_goals_by_code[code].get("goal_value") is not None
        ]
        if len(branch_goals) < 2:
            return None

        value_unit = indicator.get("value_unit")
        raw_values = [float(goal["goal_value"]) for goal in branch_goals]
        aggregated_value = aggregate_branch_goal_values(
            raw_values,
            branch_value_aggregation=branch_value_aggregation,
            value_unit=value_unit,
        )
        if aggregated_value is None:
            return None

        template = branch_goals[0]
        goal_periodicity = (template.get("goal_periodicity") or "monthly").strip() or "monthly"
        goal_mode = (template.get("goal_mode") or "standard").strip() or "standard"

        # Curva mensal: mescla os pontos das filiais em uma curva consolidada.
        # A média mensal (referência) vira apenas o goal_value de exibição —
        # nunca a base do comparable, senão meses cheios perdem o valor oficial
        # e a média × meses acumula erro de arredondamento.
        has_curve_goal = any(
            (goal.get("goal_mode") or "standard").strip().lower() == "monthly_curve"
            for goal in branch_goals
        )
        if has_curve_goal:
            merged_targets = self._merge_branch_curves(
                branch_goals=branch_goals,
                goal_periodicity=goal_periodicity,
                branch_value_aggregation=branch_value_aggregation,
                value_unit=value_unit,
            )
            if merged_targets is not None:
                aggregated_reference = self._aggregated_reference_goal(
                    branch_goals=branch_goals,
                    branch_value_aggregation=branch_value_aggregation,
                    value_unit=value_unit,
                    start_date=start_date,
                    end_date=end_date,
                    competence=competence,
                )
                if aggregated_reference is not None:
                    return {
                        "goal_label": template.get("goal_label"),
                        "goal_value": aggregated_reference,
                        "goal_periodicity": goal_periodicity,
                        "goal_mode": "monthly_curve",
                        "goal_scope_branch": "",
                        "monthly_targets": merged_targets,
                        "aggregated_from_branches": True,
                        "branch_value_aggregation": normalize_branch_value_aggregation(
                            branch_value_aggregation
                        ),
                    }

            # Fallback legado (configurações não mescláveis): referência como
            # standard mensal — comportamento anterior preservado.
            if goal_mode.lower() == "monthly_curve":
                reference_parts: list[float] = []
                for goal in branch_goals:
                    reference = self._reference_resolver.resolve_reference_goal(
                        goal_value=float(goal["goal_value"])
                        if goal.get("goal_value") is not None
                        else None,
                        goal_periodicity=(goal.get("goal_periodicity") or "monthly"),
                        goal_mode=(goal.get("goal_mode") or "monthly_curve"),
                        monthly_targets=goal.get("monthly_targets") or [],
                        start_date=start_date,
                        end_date=end_date,
                        competence=competence,
                    )
                    if reference is not None:
                        reference_parts.append(float(reference))
                if len(reference_parts) < 2:
                    return None
                aggregated_reference = aggregate_branch_goal_values(
                    reference_parts,
                    branch_value_aggregation=branch_value_aggregation,
                    value_unit=value_unit,
                )
                if aggregated_reference is None:
                    return None
                return {
                    "goal_label": template.get("goal_label"),
                    "goal_value": aggregated_reference,
                    "goal_periodicity": "monthly",
                    "goal_mode": "standard",
                    "goal_scope_branch": "",
                    "monthly_targets": [],
                    "aggregated_from_branches": True,
                }

        aggregation_mode = normalize_branch_value_aggregation(branch_value_aggregation)
        label = template.get("goal_label")
        if not label and aggregated_value is not None:
            label = str(aggregated_value)

        return {
            "goal_label": label,
            "goal_value": aggregated_value,
            "goal_periodicity": goal_periodicity,
            "goal_mode": goal_mode,
            "goal_scope_branch": "",
            "monthly_targets": template.get("monthly_targets") or [],
            "aggregated_from_branches": True,
            "branch_value_aggregation": aggregation_mode,
        }

    def _merge_branch_curves(
        self,
        *,
        branch_goals: list[dict],
        goal_periodicity: str,
        branch_value_aggregation: str | None,
        value_unit: str | None,
    ) -> list[dict] | None:
        """Mescla curvas das filiais ponto a ponto (soma/média conforme a unidade).

        Metas standard entram como curva plana de goal_value por ponto —
        equivalente exato ao prorata constante na mesma periodicidade.
        Retorna None quando as metas não são mescláveis (periodicidade
        divergente, curva vazia ou espaço de pontos desconhecido).
        """
        periodicity = (goal_periodicity or "monthly").strip().lower() or "monthly"
        if periodicity not in _FLAT_CURVE_PERIODICITIES:
            return None
        max_points = expected_monthly_curve_points(periodicity)

        points_by_goal: list[dict[int, float]] = []
        for goal in branch_goals:
            goal_per = (goal.get("goal_periodicity") or "monthly").strip().lower() or "monthly"
            if goal_per != periodicity:
                return None
            mode = (goal.get("goal_mode") or "standard").strip().lower()
            if mode == "monthly_curve":
                points: dict[int, float] = {}
                for item in goal.get("monthly_targets") or []:
                    point_number = int(item.get("month_number") or 0)
                    if 1 <= point_number <= max_points:
                        points[point_number] = float(item.get("target_value") or 0)
                if not points:
                    return None
            else:
                goal_value = float(goal.get("goal_value") or 0)
                points = {point: goal_value for point in range(1, max_points + 1)}
            points_by_goal.append(points)

        merged: list[dict] = []
        for point in range(1, max_points + 1):
            values = [points[point] for points in points_by_goal if point in points]
            if not values:
                continue
            aggregated = aggregate_branch_goal_values(
                values,
                branch_value_aggregation=branch_value_aggregation,
                value_unit=value_unit,
            )
            if aggregated is None:
                return None
            merged.append(
                {"month_number": point, "target_value": float(aggregated)}
            )
        return merged or None

    def _aggregated_reference_goal(
        self,
        *,
        branch_goals: list[dict],
        branch_value_aggregation: str | None,
        value_unit: str | None,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> float | None:
        """Meta mês consolidada de exibição: agrega a referência por filial."""
        reference_parts: list[float] = []
        for goal in branch_goals:
            reference = self._reference_resolver.resolve_reference_goal(
                goal_value=float(goal["goal_value"])
                if goal.get("goal_value") is not None
                else None,
                goal_periodicity=(goal.get("goal_periodicity") or "monthly"),
                goal_mode=(goal.get("goal_mode") or "standard"),
                monthly_targets=goal.get("monthly_targets") or [],
                start_date=start_date,
                end_date=end_date,
                competence=competence,
            )
            if reference is not None:
                reference_parts.append(float(reference))
        if len(reference_parts) < 2:
            return None
        return aggregate_branch_goal_values(
            reference_parts,
            branch_value_aggregation=branch_value_aggregation,
            value_unit=value_unit,
        )
