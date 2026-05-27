from __future__ import annotations

MONTHLY_CURVE_POINT_COUNT = 12


def is_monthly_curve_mode(goal_mode: str | None) -> bool:
    return (goal_mode or "standard").strip().lower() == "monthly_curve"


def resolve_persisted_goal_value(
    *,
    goal_mode: str,
    goal_value: float,
) -> float:
    """
    Metas em curva mensal usam apenas indicator_goal_monthly_targets.
    goal_value permanece 0 no banco (NOT NULL) para não confundir listagens/cálculo.
    """
    if is_monthly_curve_mode(goal_mode):
        return 0.0
    return max(0.0, float(goal_value or 0))


def expected_monthly_curve_points(goal_periodicity: str | None) -> int:
    periodicity = (goal_periodicity or "monthly").strip().lower()
    if periodicity == "monthly":
        return MONTHLY_CURVE_POINT_COUNT
    if periodicity == "quarterly":
        return 4
    if periodicity == "weekly":
        return 52
    if periodicity == "annual":
        return 1
    return MONTHLY_CURVE_POINT_COUNT
