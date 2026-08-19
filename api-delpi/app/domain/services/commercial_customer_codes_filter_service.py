from __future__ import annotations

from typing import Optional

# Cap to protect SQL Server parameter limits / abuse.
_MAX_CODES = 2000
_MAX_CODE_LEN = 20


class CommercialCustomerCodesFilterService:
    """TOTVS-only customer code filter. Never accepts portfolio_id / membership."""

    @staticmethod
    def normalize(value: Optional[str] | Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return None
        if isinstance(value, str):
            raw_parts = value.split(",")
        elif isinstance(value, (list, tuple)):
            raw_parts = list(value)
        else:
            # FastAPI Query() leftover from a direct handler call is not a code list.
            return None
        codes: list[str] = []
        seen: set[str] = set()
        for part in raw_parts:
            code = str(part or "").strip()
            if not code or len(code) > _MAX_CODE_LEN:
                continue
            if code in seen:
                continue
            seen.add(code)
            codes.append(code)
            if len(codes) >= _MAX_CODES:
                break
        # Empty string / whitespace-only → None (no filter).
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str) and value.strip() and not codes:
            return []
        if not codes:
            return None
        return codes

    @staticmethod
    def apply_to_query_builder(qb, column_expression: str, codes: Optional[list[str]]) -> None:
        if codes is None:
            return
        column = column_expression.strip()
        if not codes:
            qb.raw("1 = 0")
            return
        qb.in_list(column, codes)
