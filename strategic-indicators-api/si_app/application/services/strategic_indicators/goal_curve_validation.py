from __future__ import annotations

from si_app.application.services.strategic_indicators.goal_value_policy import (
    expected_monthly_curve_points,
)


def validate_curve_targets(
    monthly_targets: list,
    goal_periodicity: str,
) -> None:
    point_count = expected_monthly_curve_points(goal_periodicity)
    if len(monthly_targets) != point_count:
        raise ValueError(
            f"A curva deve conter exatamente {point_count} pontos para a periodicidade informada."
        )

    point_numbers = sorted(
        int(item.get("month_number") or 0) for item in monthly_targets
    )
    expected = list(range(1, point_count + 1))
    if point_numbers != expected:
        raise ValueError(
            f"Os pontos da curva devem ser numerados de 1 a {point_count} sem repetição."
        )

    for item in monthly_targets:
        if float(item.get("target_value") or 0) < 0:
            raise ValueError("target_value não pode ser negativo.")
