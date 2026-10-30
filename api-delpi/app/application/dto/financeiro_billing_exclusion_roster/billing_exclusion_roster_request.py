"""Typed request for the R11 billing-exclusion roster (doc 126 §17).

Contract decisions:
- ``period`` is a competence ``YYYY-MM``; the window is the full calendar
  month over the ``D2_EMISSAO`` axis;
- ``branch`` is a data filter only (PO decision, doc 49 §8);
- ``view`` selects the listing population — ``candidates`` (rows matching
  the observed historical criteria), ``out_of_criteria`` (related rows:
  group 9035 XOR TES 594 — DV-R11-04) or ``all`` (both, each total kept
  separate);
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
    VIEW_CANDIDATES,
    VIEWS,
)

_PERIOD_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_CODE_PATTERN = re.compile(r"^[0-9A-Za-z.\-/]{1,30}$")
_TES_PATTERN = re.compile(r"^[0-9A-Za-z]{1,4}$")


@dataclass(frozen=True, slots=True)
class BillingExclusionRosterRequest:
    period: str
    branch: str = BRANCH_SCOPE_ALL
    view: str = VIEW_CANDIDATES
    product_group: str | None = None
    product_code: str | None = None
    document: str | None = None
    customer_code: str | None = None
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
        view: str | None = None,
        product_group: str | None = None,
        product_code: str | None = None,
        document: str | None = None,
        customer_code: str | None = None,
        tes: str | None = None,
        include_findings: bool | None = True,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
        sort: str | None = None,
        sort_dir: str | None = None,
    ) -> "BillingExclusionRosterRequest":
        normalized_period = str(period or "").strip()
        if not _PERIOD_PATTERN.match(normalized_period):
            raise ValueError("period inválido. Use o formato YYYY-MM.")

        normalized_branch = normalize_branch_scope(branch)

        resolved_view = (view or VIEW_CANDIDATES).strip().lower()
        if resolved_view not in VIEWS:
            raise ValueError(
                "view inválido. Valores aceitos: "
                + ", ".join(sorted(VIEWS))
            )

        normalized_group = str(product_group or "").strip() or None
        if normalized_group is not None and not _CODE_PATTERN.match(
            normalized_group
        ):
            raise ValueError("product_group inválido.")

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

        normalized_customer = (
            str(customer_code or "").strip().upper() or None
        )
        if normalized_customer is not None and not _CODE_PATTERN.match(
            normalized_customer
        ):
            raise ValueError("customer_code inválido.")

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
            view=resolved_view,
            product_group=normalized_group,
            product_code=normalized_product,
            document=normalized_document,
            customer_code=normalized_customer,
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
