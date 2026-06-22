"""Classificação efetiva LMP / AMOSTRA / OUTRO e filtro de permanência."""
from __future__ import annotations

from app.application.dto.lmp.list_lmp_request import (
    LISTING_KIND_LMP,
    LISTING_KIND_OTHER,
    LISTING_KIND_SAMPLE,
)


class LmpListingKindSemanticsService:
    @staticmethod
    def effective_listing_kind(
        *,
        anchor_kind: str,
        has_sample_anchor: bool,
        sample_minutes: int,
        total_minutes: int,
        has_lmp_finalized: bool,
        min_residence_minutes: int,
        strict_residence_after_homolog: bool,
    ) -> str:
        if anchor_kind != LISTING_KIND_LMP:
            return anchor_kind

        if strict_residence_after_homolog and has_lmp_finalized:
            if total_minutes < min_residence_minutes:
                return LISTING_KIND_OTHER

        if has_sample_anchor and not has_lmp_finalized:
            if sample_minutes > 0:
                return LISTING_KIND_SAMPLE
            if total_minutes < min_residence_minutes:
                return LISTING_KIND_OTHER

        return anchor_kind

    @staticmethod
    def lmp_passes_residence_filter(
        *,
        listing_kind: str,
        total_minutes: int,
        has_sample_anchor: bool,
        has_lmp_finalized: bool,
        min_residence_minutes: int,
        strict_residence_after_homolog: bool,
    ) -> bool:
        if listing_kind in (LISTING_KIND_SAMPLE, LISTING_KIND_OTHER):
            return True
        if listing_kind != LISTING_KIND_LMP:
            return True
        if total_minutes >= min_residence_minutes:
            return True
        if strict_residence_after_homolog and has_lmp_finalized:
            return False
        return has_sample_anchor
