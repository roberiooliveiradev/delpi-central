"""Espelha regras de goalYearHelpers.ts usadas na UI de metas."""

from __future__ import annotations


def _suggest_year_before_latest(existing_years: list[int]) -> int | None:
    sorted_asc = sorted(set(existing_years))
    if not sorted_asc:
        return None
    max_year = sorted_asc[-1]
    for year in range(max_year - 1, max_year - 11, -1):
        if year not in sorted_asc:
            return year
    return max_year + 1


def _pick_source_year_for_target(existing_years: list[int], target_year: int) -> int:
    sorted_desc = sorted(set(existing_years), reverse=True)
    if not sorted_desc:
        return target_year - 1
    newer = next((year for year in sorted_desc if year > target_year), None)
    if newer is not None:
        return newer
    older = next((year for year in sorted_desc if year < target_year), None)
    if older is not None:
        return older
    return sorted_desc[0]


def test_suggest_year_before_latest_only_2026():
    assert _suggest_year_before_latest([2026]) == 2025


def test_pick_source_for_target_2025_when_2026_exists():
    assert _pick_source_year_for_target([2026], 2025) == 2026
