"""Typed request for the R10 cost-center-expenses query (doc 126 §17).

Contract decisions:
- ``period`` is a competence ``YYYY-MM``; the window is the full calendar
  month over the ``D1_DTDIGIT`` axis (never ``D1_EMISSAO``);
- ``branch`` is a data filter only (PO decision, doc 49 §8);
- ``universe`` selects the dataset scope — ``calculation`` reproduces the
  documented historical selection; ``investigation`` returns the
  in-competence rows the selection excluded. Totals never mix (doc 127);
- ``view`` filters the listing — ``all`` | ``divergences`` |
  ``unclassified``; the two last only narrow presentation, not totals;
- ``include_findings`` controls whether ``findings[]`` is materialized.
"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass

from app.domain.totvs.protheus_branches import (
    BRANCH_SCOPE_ALL,
    PROTHEUS_BRANCH_CODES,
    normalize_branch_scope,
)

from .constantes import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    SORT_DIR_ASC,
    SORT_DIRS,
    SORT_FIELD_DATE,
    SORT_FIELDS,
    UNIVERSE_CALCULATION,
    UNIVERSES,
    VIEW_ALL,
    VIEWS,
)

_PERIOD_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_CODE_PATTERN = re.compile(r"^[0-9A-Za-z.\-/]{1,30}$")
_TES_PATTERN = re.compile(r"^[0-9A-Za-z]{1,4}$")


@dataclass(frozen=True, slots=True)
class CostCenterExpensesRequest:
    period: str
    branch: str = BRANCH_SCOPE_ALL
    universe: str = UNIVERSE_CALCULATION
    view: str = VIEW_ALL
    cost_center: str | None = None
    product_code: str | None = None
    document: str | None = None
    supplier_code: str | None = None
    tes: str | None = None
    include_findings: bool = True
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
        universe: str | None = None,
        view: str | None = None,
        cost_center: str | None = None,
        product_code: str | None = None,
        document: str | None = None,
        supplier_code: str | None = None,
        tes: str | None = None,
        include_findings: bool | None = True,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
        sort: str | None = None,
        sort_dir: str | None = None,
    ) -> "CostCenterExpensesRequest":
        normalized_period = str(period or "").strip()
        if not _PERIOD_PATTERN.match(normalized_period):
            raise ValueError("period inválido. Use o formato YYYY-MM.")

        normalized_branch = normalize_branch_scope(branch)

        resolved_universe = (
            (universe or UNIVERSE_CALCULATION).strip().lower()
        )
        if resolved_universe not in UNIVERSES:
            raise ValueError(
                "universe inválido. Valores aceitos: "
                + ", ".join(sorted(UNIVERSES))
            )

        resolved_view = (view or VIEW_ALL).strip().lower()
        if resolved_view not in VIEWS:
            raise ValueError(
                "view inválido. Valores aceitos: "
                + ", ".join(sorted(VIEWS))
            )

        normalized_cc = str(cost_center or "").strip() or None
        if normalized_cc is not None and not _CODE_PATTERN.match(
            normalized_cc
        ):
            raise ValueError("cost_center inválido.")

        normalized_product = (
            str(product_code or "").strip().upper() or None
        )
        if normalized_product is not None and not _CODE_PATTERN.match(
            normalized_product
        ):
            raise ValueError("product_code inválido.")

        normalized_document = str(document or "").strip() or None
        if normalized_document is not None and not _CODE_PATTERN.match(
            normalized_document
        ):
            raise ValueError("document inválido.")

        normalized_supplier = (
            str(supplier_code or "").strip().upper() or None
        )
        if normalized_supplier is not None and not _CODE_PATTERN.match(
            normalized_supplier
        ):
            raise ValueError("supplier_code inválido.")

        normalized_tes = str(tes or "").strip().upper() or None
        if normalized_tes is not None and not _TES_PATTERN.match(
            normalized_tes
        ):
            raise ValueError("tes inválido.")

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
            universe=resolved_universe,
            view=resolved_view,
            cost_center=normalized_cc,
            product_code=normalized_product,
            document=normalized_document,
            supplier_code=normalized_supplier,
            tes=normalized_tes,
            include_findings=bool(
                include_findings if include_findings is not None else True
            ),
            page=max(int(page or DEFAULT_PAGE), 1),
            page_size=int(page_size or DEFAULT_PAGE_SIZE),
            sort=resolved_sort,
            sort_dir=resolved_dir,
        )
        request.period_end()
        return request

    def period_start(self) -> str:
        """YYYYMMDD of the first calendar day of the competence."""
        year, month = (int(part) for part in self.period.split("-"))
        return f"{year:04d}{month:02d}01"

    def period_end(self) -> str:
        """YYYYMMDD of the last calendar day of the competence."""
        year, month = (int(part) for part in self.period.split("-"))
        last_day = calendar.monthrange(year, month)[1]
        return f"{year:04d}{month:02d}{last_day:02d}"

    def requested_branches(self) -> tuple[str, ...]:
        if self.branch == BRANCH_SCOPE_ALL:
            return PROTHEUS_BRANCH_CODES
        return (self.branch,)
