"""Score e nível de alerta de recorrência na abertura de plano (Onda 6.4)."""

from __future__ import annotations

from typing import Any

from app.domain.services.quality_action_plans.pac_recurrence_alert_content_service import (
    PacRecurrenceAlertContentService,
)


class PacRecurrenceProactiveAlertService:
    @classmethod
    def compute_score(
        cls,
        *,
        plans_in_window: int,
        open_plans: int,
        total_plans: int,
    ) -> float:
        weights = PacRecurrenceAlertContentService.score_weights()
        normalizer = max(PacRecurrenceAlertContentService.total_plans_normalizer(), 1)

        window_component = min(max(plans_in_window, 0) / 4.0, 1.0) * weights["plansInWindow"]
        open_component = min(max(open_plans, 0) / 3.0, 1.0) * weights["openPlans"]
        total_component = (
            min(max(total_plans, 0) / normalizer, 1.0) * weights["totalPlansCap"]
        )

        return round(min(window_component + open_component + total_component, 1.0), 4)

    @classmethod
    def resolve_alert_level(
        cls,
        *,
        recurrence_score: float,
        plans_in_window: int,
    ) -> str:
        thresholds = PacRecurrenceAlertContentService.thresholds()

        if (
            recurrence_score >= float(thresholds["highMinScore"])
            and plans_in_window >= int(thresholds["highMinPlansInWindow"])
        ):
            return "high"

        if (
            recurrence_score >= float(thresholds["mediumMinScore"])
            and plans_in_window >= int(thresholds["mediumMinPlansInWindow"])
        ):
            return "medium"

        if plans_in_window >= 1 or recurrence_score >= 0.2:
            return "low"

        return "none"

    @classmethod
    def build_assessment(
        cls,
        *,
        recurrence_key: str | None,
        plans_in_window: int,
        open_plans: int,
        total_plans: int,
        recurrence_signals: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        score = cls.compute_score(
            plans_in_window=plans_in_window,
            open_plans=open_plans,
            total_plans=total_plans,
        )
        level = cls.resolve_alert_level(
            recurrence_score=score,
            plans_in_window=plans_in_window,
        )

        signals = recurrence_signals or {}

        return {
            "recurrence_key": recurrence_key,
            "window_months": PacRecurrenceAlertContentService.window_months(),
            "recurrence_score": score,
            "alert_level": level,
            "should_warn_before_opening": level in {"medium", "high"},
            "plans_in_window": plans_in_window,
            "open_plans": open_plans,
            "total_plans": total_plans,
            "recurrence_signals": {
                "same_product": int(signals.get("same_product") or 0),
                "same_symptom": int(signals.get("same_symptom") or 0),
                "same_root_cause_category": int(signals.get("same_root_cause_category") or 0),
            },
        }
