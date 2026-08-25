from __future__ import annotations

from typing import Optional

# Cap to protect SQL Server parameter limits / abuse.
_MAX_NAMES = 50
_MAX_NAME_LEN = 80


class CommercialCustomerNameFilterService:
    """TOTVS customer name filter (contains / LIKE). Never accepts portfolio_id."""

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

        names: list[str] = []
        seen: set[str] = set()
        for part in raw_parts:
            name = str(part or "").strip()
            if not name or len(name) > _MAX_NAME_LEN:
                continue
            key = name.casefold()
            if key in seen:
                continue
            seen.add(key)
            names.append(name)
            if len(names) >= _MAX_NAMES:
                break

        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str) and value.strip() and not names:
            return []
        if not names:
            return None
        return names

    @staticmethod
    def apply_include_to_query_builder(
        qb,
        column_expression: str,
        names: Optional[list[str]],
    ) -> None:
        """OR of case-insensitive LIKE %term% for each name term."""
        if names is None:
            return
        column = column_expression.strip()
        if not names:
            qb.raw("1 = 0")
            return
        parts: list[str] = []
        params: list[str] = []
        for name in names:
            parts.append(f"LOWER(ISNULL({column}, '')) LIKE ?")
            params.append(f"%{name.casefold()}%")
        qb.raw(f"({' OR '.join(parts)})", *params)

    @staticmethod
    def apply_exclude_to_query_builder(
        qb,
        column_expression: str,
        names: Optional[list[str]],
    ) -> None:
        """AND of NOT LIKE — exclude if name contains any term."""
        if not names:
            return
        column = column_expression.strip()
        for name in names:
            qb.raw(
                f"LOWER(ISNULL({column}, '')) NOT LIKE ?",
                f"%{name.casefold()}%",
            )
