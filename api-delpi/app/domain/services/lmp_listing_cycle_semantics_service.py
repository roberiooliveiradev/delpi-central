"""Ciclos LMP por homologação/revisão — suporte a OV reaberta no período."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, Sequence


@dataclass(frozen=True)
class LmpHomologCycleRow:
    branch: str
    sale_number: str
    homolog_revision: str
    measurement_revision: str
    homolog_date: str
    engineering_total_minutes: int
    listing_kind: str
    cycle_index: int = 0

    @property
    def row_key(self) -> tuple[str, str, str, str]:
        return (self.branch, self.sale_number, self.homolog_date, self.homolog_revision)


class LmpListingCycleSemanticsService:
    @staticmethod
    def dedupe_homolog_cycles(
        rows: Iterable[LmpHomologCycleRow],
    ) -> list[LmpHomologCycleRow]:
        """Uma linha por (filial, OV, data homolog) — revisão com maior permanência."""
        best: dict[tuple[str, str, str], LmpHomologCycleRow] = {}
        for row in rows:
            dedupe_key = (row.branch, row.sale_number, row.homolog_date)
            current = best.get(dedupe_key)
            if current is None or row.engineering_total_minutes > current.engineering_total_minutes:
                best[dedupe_key] = row
        return sorted(
            best.values(),
            key=lambda item: (item.homolog_date, item.sale_number, item.homolog_revision),
        )

    @staticmethod
    def assign_cycle_indexes(
        rows: Sequence[LmpHomologCycleRow],
    ) -> list[LmpHomologCycleRow]:
        """Numera 1..N ciclos da mesma OV dentro do período (reaberturas)."""
        per_ov: dict[tuple[str, str], int] = {}
        ordered: list[LmpHomologCycleRow] = []
        for row in sorted(rows, key=lambda item: (item.branch, item.sale_number, item.homolog_date)):
            ov_key = (row.branch, row.sale_number)
            per_ov[ov_key] = per_ov.get(ov_key, 0) + 1
            ordered.append(replace(row, cycle_index=per_ov[ov_key]))
        return ordered

    @staticmethod
    def pick_measurement_revision(
        revision_minutes: dict[str, int],
        *,
        homolog_revision: str,
    ) -> str:
        """Revisão com maior minutos no ciclo; fallback = revisão da homolog."""
        if not revision_minutes:
            return homolog_revision
        return max(revision_minutes.items(), key=lambda item: (item[1], item[0]))[0]
