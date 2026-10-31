"""Request for the R12/R15 closing-state read (doc 129 §2.1)."""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta

_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

# Window covering the delayed virada observed in evidence (f01 set/2026
# snapshot landed 21/10 — doc 85 §14 BR-R15-002).
EVIDENCE_WINDOW_DAYS = 45


@dataclass(frozen=True, slots=True)
class ClosingStateRequest:
    period: str
    branch: str

    @classmethod
    def from_query(cls, *, period: str, branch: str | None):
        period = (period or "").strip()
        if not _PERIOD_RE.match(period):
            raise ValueError(
                "Parâmetro 'period' deve estar no formato YYYY-MM."
            )
        branch = (branch or "all").strip().lower()
        if branch not in ("all", "01", "02"):
            raise ValueError(
                "Parâmetro 'branch' deve ser all, 01 ou 02."
            )
        return cls(period=period, branch=branch)

    def snapshot_date(self) -> str:
        """Last calendar day of the competence — SB9 ``B9_DATA`` anchor."""
        year, month = (int(p) for p in self.period.split("-"))
        last_day = calendar.monthrange(year, month)[1]
        return f"{year:04d}{month:02d}{last_day:02d}"

    def snapshot_date_iso(self) -> str:
        ref = self.snapshot_date()
        return f"{ref[:4]}-{ref[4:6]}-{ref[6:8]}"

    def evidence_window(self) -> tuple[str, str]:
        """[competence start, snapshot + 45d] as TTAT_DTIME strings."""
        year, month = (int(p) for p in self.period.split("-"))
        last_day = calendar.monthrange(year, month)[1]

        start = date(year, month, 1)
        end = date(year, month, last_day) + timedelta(
            days=EVIDENCE_WINDOW_DAYS
        )
        return (
            f"{start.isoformat()} 00:00:00",
            f"{end.isoformat()} 23:59:59",
        )

    def requested_branches(self) -> tuple[str, ...]:
        return ("01", "02") if self.branch == "all" else (self.branch,)
