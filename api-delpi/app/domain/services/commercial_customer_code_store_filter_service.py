from __future__ import annotations

from typing import Optional

# Cap to protect SQL Server parameter limits / abuse (aligned with codes filter).
_MAX_PAIRS = 2000
_MAX_CODE_LEN = 20
_MAX_STORE_LEN = 8


class CommercialCustomerCodeStoreFilterService:
    """TOTVS-only (customer code, store) pair filter. Never accepts portfolio_id."""

    @staticmethod
    def normalize(
        value: Optional[str] | Optional[list[str]] | Optional[list[tuple[str, str]]],
    ) -> Optional[list[tuple[str, str]]]:
        if value is None:
            return None
        if isinstance(value, str):
            raw_parts = value.split(",")
        elif isinstance(value, (list, tuple)):
            raw_parts = list(value)
        else:
            return None

        pairs: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for part in raw_parts:
            if isinstance(part, (tuple, list)) and len(part) == 2:
                code = str(part[0] or "").strip()
                store = str(part[1] or "").strip()
            else:
                token = str(part or "").strip()
                if not token or "|" not in token:
                    continue
                code_raw, store_raw = token.split("|", 1)
                code = code_raw.strip()
                store = store_raw.strip()
            if not code or not store:
                continue
            if len(code) > _MAX_CODE_LEN or len(store) > _MAX_STORE_LEN:
                continue
            key = (code, store)
            if key in seen:
                continue
            seen.add(key)
            pairs.append(key)
            if len(pairs) >= _MAX_PAIRS:
                break

        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str) and value.strip() and not pairs:
            return []
        if not pairs:
            return None
        return pairs

    @staticmethod
    def apply_to_query_builder(
        qb,
        code_column: str,
        store_column: str,
        pairs: Optional[list[tuple[str, str]]],
    ) -> None:
        if pairs is None:
            return
        code_col = code_column.strip()
        store_col = store_column.strip()
        if not pairs:
            qb.raw("1 = 0")
            return
        parts: list[str] = []
        params: list[str] = []
        for code, store in pairs:
            parts.append(f"({code_col} = ? AND {store_col} = ?)")
            params.extend([code, store])
        qb.raw(f"({' OR '.join(parts)})", *params)
