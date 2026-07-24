"""Matching fiscal de conciliação — chave homologada SF1."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable, Sequence


@dataclass(frozen=True, slots=True)
class FiscalMatchKey:
    branch_code: str
    supplier_code: str
    supplier_store: str
    document_match_key: str
    series: str


def fiscal_match_key_from_mapping(row: dict[str, Any]) -> FiscalMatchKey:
    return FiscalMatchKey(
        branch_code=str(row.get("branch_code") or "").strip(),
        supplier_code=str(row.get("supplier_code") or "").strip(),
        supplier_store=str(row.get("supplier_store") or "").strip(),
        document_match_key=str(row.get("document_match_key") or "").strip(),
        series=str(row.get("series") or "").strip().upper(),
    )


def parse_erp_entry_date(raw: Any) -> date | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    text = str(raw).strip()
    if not text:
        return None
    if len(text) >= 8 and text[:8].isdigit():
        try:
            return date(int(text[0:4]), int(text[4:6]), int(text[6:8]))
        except ValueError:
            return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


@dataclass(frozen=True, slots=True)
class MatchDecision:
    request: dict[str, Any]
    outcome: str  # matched | not_found | ambiguous
    sf1_row: dict[str, Any] | None = None


def classify_candidates(
    candidates: Sequence[dict[str, Any]],
    sf1_rows: Iterable[dict[str, Any]],
) -> list[MatchDecision]:
    by_key: dict[FiscalMatchKey, list[dict[str, Any]]] = defaultdict(list)
    for row in sf1_rows:
        by_key[fiscal_match_key_from_mapping(row)].append(row)

    decisions: list[MatchDecision] = []
    for candidate in candidates:
        key = fiscal_match_key_from_mapping(candidate)
        matches = by_key.get(key, [])
        if len(matches) == 0:
            decisions.append(
                MatchDecision(request=candidate, outcome="not_found")
            )
        elif len(matches) > 1:
            decisions.append(
                MatchDecision(request=candidate, outcome="ambiguous")
            )
        else:
            decisions.append(
                MatchDecision(
                    request=candidate,
                    outcome="matched",
                    sf1_row=matches[0],
                )
            )
    return decisions
