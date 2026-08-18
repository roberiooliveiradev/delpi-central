"""Aggregate open/won opportunity counts by seller (pure)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence


class OpportunityCollaboratorSummaryService:
    def summarize(
        self,
        items: Sequence[Mapping[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        buckets: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "sellerCode": "",
                "sellerName": "",
                "openCount": 0,
                "wonCount": 0,
                "lostCount": 0,
                "totalCount": 0,
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
        rows = list(buckets.values())
        rows.sort(key=lambda row: (-int(row["totalCount"]), str(row["sellerCode"])))
        return rows
