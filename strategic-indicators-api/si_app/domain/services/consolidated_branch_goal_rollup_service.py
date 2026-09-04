"""Rollup canônico de metas por filial → visão consolidada (01+02).

Agrega referências (Meta mês) em curva mensal e devolve goal_mode=standard
para o serialize aplicar MTD uma única vez — evita dupla proporção.
"""

from __future__ import annotations

from typing import Any, Protocol

from si_app.shared.consolidated_value_aggregation import (
    aggregate_branch_goal_values,
    is_source_consolidated_mode,
    normalize_branch_value_aggregation,
)
from si_app.shared.goal_scope import BRANCH_UNIT_CODES


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
        - monthly_curve: soma/média das Meta mês → standard (MTD no serialize)
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

        # Curva mensal: agrega a meta de referência (Meta mês) por filial.
        # Nunca embutir o comparable já rateado como goal_value + mode standard —
        # o serialize recalcularia a fração MTD e aplicaria proporção em dobro.
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
