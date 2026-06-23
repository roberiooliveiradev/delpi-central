"""Semântica de inclusão no período — dashboard LMP (desacoplado do SQL)."""
from __future__ import annotations

from app.application.dto.lmp.list_lmp_request import ListLMPRequest

ANCHOR_IN_PERIOD = "anchor_in_period"
ANCHOR_OR_FIRST_ENG = "anchor_or_first_eng"
HOMOLOG_IN_PERIOD = "homolog_in_period"
HOMOLOG_CYCLES_IN_PERIOD = "homolog_cycles_in_period"
WORK_MONTH_LMP = "work_month_lmp"

SUPPORTED_POLICIES = frozenset(
    {
        ANCHOR_IN_PERIOD,
        ANCHOR_OR_FIRST_ENG,
        HOMOLOG_IN_PERIOD,
        HOMOLOG_CYCLES_IN_PERIOD,
        WORK_MONTH_LMP,
    },
)


class LmpPeriodInclusionSemanticsService:
    @staticmethod
    def normalize_policy(raw: str | None) -> str:
        if raw is None or str(raw).strip() == "":
            return WORK_MONTH_LMP
        normalized = str(raw).strip().lower()
        if normalized not in SUPPORTED_POLICIES:
            raise ValueError(
                "period_inclusion_policy inválida. "
                f"Valores aceitos: {WORK_MONTH_LMP}, {ANCHOR_IN_PERIOD}, "
                f"{HOMOLOG_CYCLES_IN_PERIOD}, {ANCHOR_OR_FIRST_ENG}, {HOMOLOG_IN_PERIOD}."
            )
        return normalized

    @staticmethod
    def uses_homolog_cycle_listing(policy: str) -> bool:
        return (
            LmpPeriodInclusionSemanticsService.normalize_policy(policy)
            == HOMOLOG_CYCLES_IN_PERIOD
        )

    @staticmethod
    def uses_per_revision_candidate_listing(policy: str) -> bool:
        resolved = LmpPeriodInclusionSemanticsService.normalize_policy(policy)
        return resolved in (HOMOLOG_CYCLES_IN_PERIOD, WORK_MONTH_LMP)

    @staticmethod
    def uses_work_month_lmp_listing(policy: str) -> bool:
        return (
            LmpPeriodInclusionSemanticsService.normalize_policy(policy)
            == WORK_MONTH_LMP
        )

    @staticmethod
    def requires_first_eng_join(policy: str) -> bool:
        return LmpPeriodInclusionSemanticsService.normalize_policy(policy) == ANCHOR_OR_FIRST_ENG

    @staticmethod
    def build_candidate_period_predicate(
        *,
        policy: str,
        anchor_date_sql: str,
        first_eng_date_sql: str = "F.FIRST_ENG_DATE",
        homolog_date_sql: str = "LF.ANCHOR_START_DATE",
        where_anchor: str,
        where_first_eng: str,
        where_homolog: str,
    ) -> str:
        """Monta predicado SQL já parametrizado (cláusulas WHERE do QueryBuilder)."""
        resolved = LmpPeriodInclusionSemanticsService.normalize_policy(policy)
        if resolved in (ANCHOR_IN_PERIOD, WORK_MONTH_LMP):
            if not where_anchor:
                return "1=0"
            return where_anchor
        if resolved == HOMOLOG_IN_PERIOD:
            if not where_homolog:
                return "1=0"
            return where_homolog.replace(homolog_date_sql, homolog_date_sql)
        if not where_anchor and not where_first_eng:
            return "1=1"
        if not where_anchor:
            return where_first_eng
        if not where_first_eng:
            return where_anchor
        return f"(({where_anchor}) OR ({where_first_eng}))"

    @staticmethod
    def build_homolog_date_field_sql() -> str:
        return "LF.ANCHOR_START_DATE"

    @staticmethod
    def has_period_filter(request: ListLMPRequest) -> bool:
        return bool(request.date_start and request.date_end)
