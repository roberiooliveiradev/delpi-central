"""Aggregate open/won opportunity counts by seller (pure)."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any, Mapping, Sequence


def _parse_iso_date(raw: Any) -> date | None:
    text = str(raw or "").strip()[:10]
    if len(text) != 10:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _age_days(proposal_date: Any, *, as_of: date) -> int | None:
    parsed = _parse_iso_date(proposal_date)
    if parsed is None:
        return None
    return max(0, (as_of - parsed).days)


class OpportunityCollaboratorSummaryService:
    def summarize(
        self,
        items: Sequence[Mapping[str, Any]] | None,
        *,
        as_of: date | None = None,
    ) -> list[dict[str, Any]]:
        today = as_of or date.today()
        buckets: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "sellerCode": "",
                "sellerName": "",
                "openCount": 0,
                "wonCount": 0,
                "lostCount": 0,
                "totalCount": 0,
                "ageDaysSum": 0,
                "ageDaysSamples": 0,
            }
        )
        for raw in items or ():
            if not isinstance(raw, Mapping):
                continue
            code = str(raw.get("seller_code") or raw.get("sellerCode") or "").strip() or "_"
            name = str(raw.get("seller_name") or raw.get("sellerName") or "").strip()
            category = str(raw.get("status_category") or raw.get("statusCategory") or "").strip()
            bucket = buckets[code]
            bucket["sellerCode"] = "" if code == "_" else code
            if name:
                bucket["sellerName"] = name
            bucket["totalCount"] += 1
            if category == "won":
                bucket["wonCount"] += 1
            elif category == "lost":
                bucket["lostCount"] += 1
            elif category == "open":
                bucket["openCount"] += 1
            age = _age_days(raw.get("proposal_date") or raw.get("proposalDate"), as_of=today)
            if age is not None:
                bucket["ageDaysSum"] += age
                bucket["ageDaysSamples"] += 1
        rows: list[dict[str, Any]] = []
        for bucket in buckets.values():
            samples = int(bucket.pop("ageDaysSamples"))
            age_sum = int(bucket.pop("ageDaysSum"))
            bucket["ageDaysAvg"] = round(age_sum / samples, 1) if samples else None
            rows.append(bucket)
        rows.sort(key=lambda row: (-int(row["totalCount"]), str(row["sellerCode"])))
        return rows
