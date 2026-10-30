"""Typed request for the R06 stock-kardex movement query (doc 122 §4).

Contract decisions:
- ``period`` is a competence ``YYYY-MM``; the movement window is the full
  calendar month and the opening balance is the SB9 snapshot of the
  PREVIOUS month-end — never silently substituted;
- ``branch`` is a data filter only (PO decision, doc 49 §8);
- ``warehouse`` accepts one or more local codes (comma-separated);
- ``product_code`` / ``product_type`` narrow the MATR910 population;
- ``document_kind`` selects the movement universe (``all`` | ``invent``);
- ``movement_kind`` filters the printed column (``entry`` | ``output``).
"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta

from app.domain.totvs.protheus_branches import (
    BRANCH_SCOPE_ALL,
    PROTHEUS_BRANCH_CODES,
    normalize_branch_scope,
)

from .constantes import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    DOCUMENT_KIND_ALL,
    DOCUMENT_KINDS,
    MOVEMENT_KINDS,
    SORT_DIR_ASC,
    SORT_DIRS,
    SORT_FIELD_DATE,
    SORT_FIELDS,
)

_PERIOD_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_WAREHOUSE_PATTERN = re.compile(r"^[0-9A-Za-z]{1,10}$")
_PRODUCT_PATTERN = re.compile(r"^[0-9A-Za-z.\-/]{1,30}$")
_PRODUCT_TYPE_PATTERN = re.compile(r"^[0-9A-Za-z]{1,4}$")


@dataclass(frozen=True, slots=True)
class StockKardexQueryRequest:
    period: str
    branch: str = BRANCH_SCOPE_ALL
    warehouse: str | None = None
    product_code: str | None = None
    product_type: str | None = None
    document_kind: str = DOCUMENT_KIND_ALL
    movement_kind: str | None = None
    page: int = DEFAULT_PAGE
    page_size: int = DEFAULT_PAGE_SIZE
    sort: str = SORT_FIELD_DATE
    sort_dir: str = SORT_DIR_ASC

    @classmethod
    def from_query(
        cls,
        *,
        period: str | None,
        branch: str | None = None,
        warehouse: str | None = None,
        product_code: str | None = None,
        product_type: str | None = None,
        document_kind: str | None = None,
        movement_kind: str | None = None,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
        sort: str | None = None,
        sort_dir: str | None = None,
    ) -> "StockKardexQueryRequest":
        normalized_period = str(period or "").strip()
        if not _PERIOD_PATTERN.match(normalized_period):
            raise ValueError("period inválido. Use o formato YYYY-MM.")

        normalized_branch = normalize_branch_scope(branch)

        normalized_warehouse = str(warehouse or "").strip() or None
        if normalized_warehouse is not None:
            for code in normalized_warehouse.split(","):
                if not _WAREHOUSE_PATTERN.match(code.strip()):
                    raise ValueError(
                        "warehouse inválido. Use códigos alfanuméricos "
                        "(1–10), separados por vírgula."
                    )
            normalized_warehouse = ",".join(
                code.strip().upper()
                for code in normalized_warehouse.split(",")
            )

        normalized_product = str(product_code or "").strip().upper() or None
        if normalized_product is not None and not _PRODUCT_PATTERN.match(
            normalized_product
        ):
            raise ValueError("product_code inválido.")

        normalized_type = str(product_type or "").strip().upper() or None
        if normalized_type is not None and not _PRODUCT_TYPE_PATTERN.match(
            normalized_type
        ):
            raise ValueError("product_type inválido.")

        resolved_kind = (document_kind or DOCUMENT_KIND_ALL).strip().lower()
        if resolved_kind not in DOCUMENT_KINDS:
            raise ValueError(
                "document_kind inválido. Valores aceitos: "
                + ", ".join(sorted(DOCUMENT_KINDS))
            )

        resolved_kind_filter = (
            str(movement_kind or "").strip().lower() or None
        )
        if resolved_kind_filter is not None and (
            resolved_kind_filter not in MOVEMENT_KINDS
        ):
            raise ValueError(
                "movement_kind inválido. Valores aceitos: "
                + ", ".join(sorted(MOVEMENT_KINDS))
            )

        resolved_sort = (sort or SORT_FIELD_DATE).strip().lower()
        if resolved_sort not in SORT_FIELDS:
            raise ValueError(
                "sort inválido. Valores aceitos: "
                + ", ".join(sorted(SORT_FIELDS))
            )
        resolved_dir = (sort_dir or SORT_DIR_ASC).strip().lower()
        if resolved_dir not in SORT_DIRS:
            raise ValueError("sort_dir inválido. Use asc ou desc.")

        request = cls(
            period=normalized_period,
            branch=normalized_branch,
            warehouse=normalized_warehouse,
            product_code=normalized_product,
            product_type=normalized_type,
            document_kind=resolved_kind,
            movement_kind=resolved_kind_filter,
            page=max(int(page or DEFAULT_PAGE), 1),
            page_size=int(page_size or DEFAULT_PAGE_SIZE),
            sort=resolved_sort,
            sort_dir=resolved_dir,
        )
        request.reference_date()
        return request

    def period_start(self) -> str:
        """YYYYMMDD of the first calendar day of the competence."""
        year, month = (int(part) for part in self.period.split("-"))
        return f"{year:04d}{month:02d}01"

    def period_start_iso(self) -> str:
        start = self.period_start()
        return f"{start[0:4]}-{start[4:6]}-{start[6:8]}"

    def reference_date(self) -> str:
        """YYYYMMDD of the last calendar day of the competence."""
        year, month = (int(part) for part in self.period.split("-"))
        last_day = calendar.monthrange(year, month)[1]
        return f"{year:04d}{month:02d}{last_day:02d}"

    def reference_date_iso(self) -> str:
        ref = self.reference_date()
        return f"{ref[0:4]}-{ref[4:6]}-{ref[6:8]}"

    def as_of_boundary(self) -> str:
        """YYYYMMDD of the FIRST day after the competence — the
        exclusive temporal boundary for post-close cost reconstruction
        (doc 122 §5.2, rework 017). The competence is closed at the end
        of ``reference_date``; the earliest ``TTAT_COLD`` logged at or
        after this instant is the cost the field carried at the
        competence end (post-close), matching the MATR910 emission
        convention."""
        year, month = (int(part) for part in self.period.split("-"))
        end = date(year, month, calendar.monthrange(year, month)[1])
        boundary = end + timedelta(days=1)
        return boundary.strftime("%Y%m%d")

    def as_of_boundary_iso(self) -> str:
        ref = self.as_of_boundary()
        return f"{ref[0:4]}-{ref[4:6]}-{ref[6:8]}"

    def opening_snapshot_date(self) -> str:
        """YYYYMMDD of the PREVIOUS month-end — the SB9 closing that
        seeds the opening balance (MATR910 ``CalcEst(prod,local,par05)``
        reads the position at the period start)."""
        year, month = (int(part) for part in self.period.split("-"))
        if month == 1:
            year, month = year - 1, 12
        else:
            month -= 1
        last_day = calendar.monthrange(year, month)[1]
        return f"{year:04d}{month:02d}{last_day:02d}"

    def opening_snapshot_date_iso(self) -> str:
        ref = self.opening_snapshot_date()
        return f"{ref[0:4]}-{ref[4:6]}-{ref[6:8]}"

    def requested_branches(self) -> tuple[str, ...]:
        if self.branch == BRANCH_SCOPE_ALL:
            return PROTHEUS_BRANCH_CODES
        return (self.branch,)

    def requested_warehouses(self) -> tuple[str, ...] | None:
        """Concrete local codes, or ``None`` for the full MATR910 scope."""
        if not self.warehouse:
            return None
        return tuple(self.warehouse.split(","))
