"""Narrativa e insights para resultados SQL de programação de produção (SC2010)."""

from __future__ import annotations

from collections import Counter
from typing import Callable

from app.domain.services.chat_sql_production_schedule_date_service import (
    ResolvedProductionScheduleDate,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)

_PREVIEW_MAX = 3
_LARGE_SET_THRESHOLD = 20
_FAMILY_PREFIX_LEN = 4
_TOP_FAMILIES = 3


class ChatSqlProductionSchedulePresentationService:
    @classmethod
    def build_linhas(
        cls,
        rows: list[dict],
        *,
        schedule: ResolvedProductionScheduleDate | None = None,
        record_total: int | None = None,
        include_branch_breakdown: bool = False,
        format_row: Callable[[dict], str] | None = None,
    ) -> list[str]:
        if not rows:
            return []

        shown = len(rows)
        total = record_total if record_total is not None and record_total >= shown else shown
        label = (
            schedule.label
            if schedule
            else ExternalActionResponseContentService.get("temporal", "today", default="hoje")
        )

        linhas: list[str] = [
            cls._format("scopeIntro", label=label),
        ]

        if total > shown:
            linhas.append(
                cls._format("summaryShown", shown=str(shown))
                + cls._format("summaryTotalSuffix", total=str(total))
            )
        else:
            linhas.append(cls._format("summaryShownOnly", shown=str(shown)))

        distinct_codes = cls._distinct_product_codes(rows)

        if distinct_codes:
            linhas.append(
                cls._format("distinctProducts", count=str(distinct_codes)),
            )

        branch_line = cls._branch_breakdown_line(rows, enabled=include_branch_breakdown)

        if branch_line:
            linhas.append(branch_line)

        families_line = cls._top_families_line(rows)

        if families_line:
            linhas.append(families_line)

        if total >= _LARGE_SET_THRESHOLD:
            linhas.append(cls._text("largeSetHint"))

        preview_rows = [row for row in rows[:_PREVIEW_MAX] if isinstance(row, dict)]

        if preview_rows and format_row is not None:
            linhas.append(cls._text("previewHeader"))

            for row in preview_rows:
                line = format_row(row)

                if line:
                    linhas.append(line)

            remaining = shown - len(preview_rows)

            if remaining > 0:
                linhas.append(
                    cls._format("truncatedSample", count=str(remaining)),
                )

        return linhas

    @classmethod
    def _distinct_product_codes(cls, rows: list[dict]) -> int:
        codes: set[str] = set()

        for row in rows:
            if not isinstance(row, dict):
                continue

            code = str(row.get("COD_PRODUTO") or row.get("cod_produto") or "").strip()

            if code:
                codes.add(code)

        return len(codes)

    @classmethod
    def _branch_breakdown_line(cls, rows: list[dict], *, enabled: bool) -> str | None:
        if not enabled:
            return None

        counts: Counter[str] = Counter()

        for row in rows:
            if not isinstance(row, dict):
                continue

            branch = str(row.get("FILIAL") or row.get("filial") or "").strip()

            if branch:
                counts[branch] += 1

        if not counts:
            return None

        items = [
            cls._format("branchItem", branch=branch, count=str(count))
            for branch, count in sorted(counts.items())
        ]

        return cls._text("branchBreakdownHeader") + " " + cls._text("branchSeparator").join(items)

    @classmethod
    def _top_families_line(cls, rows: list[dict]) -> str | None:
        prefixes: Counter[str] = Counter()

        for row in rows:
            if not isinstance(row, dict):
                continue

            code = str(row.get("COD_PRODUTO") or row.get("cod_produto") or "").strip()
            digits = "".join(ch for ch in code if ch.isdigit())

            if len(digits) >= _FAMILY_PREFIX_LEN:
                prefixes[digits[:_FAMILY_PREFIX_LEN]] += 1

        if not prefixes:
            return None

        top = prefixes.most_common(_TOP_FAMILIES)
        families = cls._text("familySeparator").join(
            cls._format("familyItem", prefix=prefix, count=str(count))
            for prefix, count in top
        )

        return cls._format("topFamiliesHeader", families=families)

    @classmethod
    def _format(cls, key: str, **values: str) -> str:
        return ExternalActionResponseContentService.format(
            "productionSchedule",
            "narrative",
            key,
            **values,
        )

    @classmethod
    def _text(cls, key: str, **values: str) -> str:
        formatted = cls._format(key, **values)

        if formatted:
            return formatted

        return ExternalActionResponseContentService.get(
            "productionSchedule",
            "narrative",
            key,
            default="",
        )
