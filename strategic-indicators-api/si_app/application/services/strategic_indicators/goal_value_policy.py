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


def parse_year_from_competence(competence: str | None) -> int | None:
    normalized = (competence or "").strip()
    if len(normalized) >= 4 and normalized[:4].isdigit():
        return int(normalized[:4])
    return None


def calendar_month_to_curve_point(
    goal_periodicity: str,
    month: int,
    *,
    year: int,
) -> int:
    periodicity = (goal_periodicity or "monthly").strip().lower()
    if periodicity == "quarterly":
        return (month - 1) // 3 + 1
    if periodicity == "annual":
        return 1
    if periodicity == "weekly":
        from datetime import date

        safe_month = min(max(month, 1), 12)
        return date(year, safe_month, 15).isocalendar()[1]
    return month


def curve_point_indices_for_calendar_months(
    goal_periodicity: str,
    calendar_months: list[int],
    *,
    year: int | None = None,
) -> list[int]:
    resolved_year = year or 2026
    indices: set[int] = set()
    for month in calendar_months:
        if month < 1 or month > 12:
            continue
        indices.add(
            calendar_month_to_curve_point(
                goal_periodicity,
                month,
                year=resolved_year,
            )
        )
    return sorted(indices)
