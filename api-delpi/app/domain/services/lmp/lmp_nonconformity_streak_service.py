"""Cálculo de dias sem NC em LMP (streak atual e recorde)."""

from app.domain.services.calendar_occurrence_streak_service import (
    compute_occurrence_streak as compute_lmp_nc_streak,
)

__all__ = ["compute_lmp_nc_streak"]
