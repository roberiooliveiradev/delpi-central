from __future__ import annotations

from typing import Optional

# Cap aligned with the customer-code filter (SQL Server parameter limits).
_MAX_CENTERS = 2000
_MAX_CENTER_LEN = 20


class CommercialCustomerCenterFilterService:
    """TOTVS customer-center filter (SA7.A7_XCENT). Never accepts portfolio_id."""

    @staticmethod
    def normalize(value: Optional[str] | Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return None
        if isinstance(value, str):
            raw_parts = value.split(",")
        elif isinstance(value, (list, tuple)):
            raw_parts = list(value)
        else:
            return None

        centers: list[str] = []
        seen: set[str] = set()
        for part in raw_parts:
            center = str(part or "").strip()
            if not center or len(center) > _MAX_CENTER_LEN:
                continue
            key = center.casefold()
            if key in seen:
                continue
            seen.add(key)
            centers.append(center)
            if len(centers) >= _MAX_CENTERS:
                break

        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str) and value.strip() and not centers:
            return []
        if not centers:
            return None
        return sorted(centers, key=str.casefold)

    @staticmethod
    def apply_to_query_builder(
        qb,
        column_expression: str,
        centers: Optional[list[str]],
    ) -> None:
        if centers is None:
            return
        column = column_expression.strip()
        if not centers:
            qb.raw("1 = 0")
            return
        qb.in_list(column, centers)
