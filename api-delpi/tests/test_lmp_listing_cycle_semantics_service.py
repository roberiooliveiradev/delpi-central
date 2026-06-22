from __future__ import annotations

import pytest

from app.domain.services.lmp_listing_cycle_semantics_service import (
    LmpHomologCycleRow,
    LmpListingCycleSemanticsService,
)
from app.domain.services.lmp_listing_kind_semantics_service import (
    LmpListingKindSemanticsService,
)
from app.domain.services.lmp_period_inclusion_semantics_service import (
    ANCHOR_OR_FIRST_ENG,
    HOMOLOG_IN_PERIOD,
    LmpPeriodInclusionSemanticsService,
)
from tests.fixtures.lmp_listing_cycle_regression_cases import (
    KIND_REGRESSION,
    MAY_2026_RAW_CYCLES,
    Q2_061_CYCLES,
)


def test_period_predicate_homolog_in_period_uses_homolog_only() -> None:
    sql = LmpPeriodInclusionSemanticsService.build_candidate_period_predicate(
        policy=HOMOLOG_IN_PERIOD,
        anchor_date_sql="L.ANCHOR_START_DATE",
        homolog_date_sql="LF.ANCHOR_START_DATE",
        where_anchor="L.ANCHOR_START_DATE >= ?",
        where_first_eng="F.FIRST_ENG_DATE >= ?",
        where_homolog="LF.ANCHOR_START_DATE >= ?",
    )
    assert sql == "LF.ANCHOR_START_DATE >= ?"
    assert "FIRST_ENG" not in sql


def test_period_predicate_anchor_or_first_eng_keeps_or() -> None:
    sql = LmpPeriodInclusionSemanticsService.build_candidate_period_predicate(
        policy=ANCHOR_OR_FIRST_ENG,
        anchor_date_sql="L.ANCHOR_START_DATE",
        where_anchor="L.ANCHOR_START_DATE >= ?",
        where_first_eng="F.FIRST_ENG_DATE >= ?",
        where_homolog="LF.ANCHOR_START_DATE >= ?",
    )
    assert " OR " in sql
    assert "L.ANCHOR_START_DATE" in sql
    assert "F.FIRST_ENG_DATE" in sql


@pytest.mark.parametrize("case", KIND_REGRESSION, ids=[c["id"] for c in KIND_REGRESSION])
def test_listing_kind_regression_cases(case: dict) -> None:
    kind = LmpListingKindSemanticsService.effective_listing_kind(
        anchor_kind=case["anchor_kind"],
        has_sample_anchor=case["has_sample"],
        sample_minutes=case["sample_minutes"],
        total_minutes=case["total_minutes"],
        has_lmp_finalized=case["has_lmp_finalized"],
        min_residence_minutes=30,
        strict_residence_after_homolog=case["strict"],
    )
    passes = LmpListingKindSemanticsService.lmp_passes_residence_filter(
        listing_kind=kind,
        total_minutes=case["total_minutes"],
        has_sample_anchor=case["has_sample"],
        has_lmp_finalized=case["has_lmp_finalized"],
        min_residence_minutes=30,
        strict_residence_after_homolog=case["strict"],
    )
    assert kind == case["expected_kind"]
    assert passes == case["passes_residence"]


def test_dedupe_102_uses_measurement_revision_with_more_minutes() -> None:
    cycles = LmpListingCycleSemanticsService.dedupe_homolog_cycles(MAY_2026_RAW_CYCLES)
    ov102 = next(row for row in cycles if row.sale_number == "000102")
    assert ov102.measurement_revision == "03"
    assert ov102.engineering_total_minutes == 1644
    assert ov102.listing_kind == "LMP"


def test_dedupe_may_extras_561_2871_outro() -> None:
    cycles = LmpListingCycleSemanticsService.dedupe_homolog_cycles(MAY_2026_RAW_CYCLES)
    by_ov = {row.sale_number: row for row in cycles}
    assert by_ov["003561"].listing_kind == "OUTRO"
    assert by_ov["002871"].listing_kind == "OUTRO"
    assert by_ov["000087"].listing_kind == "LMP"


def test_assign_cycle_indexes_090_two_cycles_in_may() -> None:
    cycles = LmpListingCycleSemanticsService.dedupe_homolog_cycles(MAY_2026_RAW_CYCLES)
    indexed = LmpListingCycleSemanticsService.assign_cycle_indexes(cycles)
    cycles_090 = [row for row in indexed if row.sale_number == "000090"]
    assert len(cycles_090) == 2
    assert cycles_090[0].cycle_index == 1
    assert cycles_090[1].cycle_index == 2
    assert cycles_090[0].homolog_date == "20260506"
    assert cycles_090[1].homolog_date == "20260515"


def test_assign_cycle_indexes_061_three_cycles_in_q2() -> None:
    indexed = LmpListingCycleSemanticsService.assign_cycle_indexes(Q2_061_CYCLES)
    assert len(indexed) == 3
    assert [row.cycle_index for row in indexed] == [1, 2, 3]
    assert indexed[0].listing_kind == "OUTRO"
    assert indexed[1].listing_kind == "LMP"
    assert indexed[2].listing_kind == "LMP"


def test_pick_measurement_revision_prefers_max_minutes() -> None:
    picked = LmpListingCycleSemanticsService.pick_measurement_revision(
        {"03": 1644, "04": 0},
        homolog_revision="04",
    )
    assert picked == "03"
