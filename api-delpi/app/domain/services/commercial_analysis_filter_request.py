from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

ALLOWED_ANALYSIS_GRANULARITIES = frozenset({"day", "week", "month", "year"})
ALLOWED_ANALYSIS_GROUP_BY = frozenset({"none", "customer", "branch"})
ALLOWED_ANALYSIS_BRANCHES = frozenset({"01", "02"})
ALLOWED_INCLUDE_FLAGS = frozenset({"portfolio"})


@dataclass
class CommercialAnalysisFilterRequest:
    """Shared filters for consolidated commercial analysis routes (ROL / OTD)."""

    start_date: Optional[str] = None
    end_date: Optional[str] = None
    granularity: str = "week"
    branch: Optional[str] = None
    customer_segment: Optional[str] = None
    customer_codes: Optional[list[str]] = None
    customer_names: Optional[list[str]] = None
    exclude_customer_codes: Optional[list[str]] = None
    exclude_customer_names: Optional[list[str]] = None
    group_by: str = "customer"
    page: int = 1
    page_size: int = 50
    include_flags: frozenset[str] = field(default_factory=frozenset)

    def validate(self) -> None:
        granularity = (self.granularity or "").strip().lower()
        if granularity not in ALLOWED_ANALYSIS_GRANULARITIES:
            raise ValueError("granularity deve ser day, week, month ou year.")
        self.granularity = granularity

        group_by = (self.group_by or "customer").strip().lower()
        if group_by not in ALLOWED_ANALYSIS_GROUP_BY:
            raise ValueError("group_by deve ser none, customer ou branch.")
        self.group_by = group_by

        if self.branch is not None:
            branch = str(self.branch).strip()
            if branch not in ALLOWED_ANALYSIS_BRANCHES:
                raise ValueError("branch deve ser 01, 02 ou omitido (consolidado).")
            self.branch = branch

        page = int(self.page)
        page_size = int(self.page_size)
        if page < 1:
            raise ValueError("page deve ser >= 1.")
        if page_size < 1 or page_size > 500:
            raise ValueError("page_size deve estar entre 1 e 500.")
        self.page = page
        self.page_size = page_size

        flags = frozenset(
            str(flag).strip().lower()
            for flag in (self.include_flags or frozenset())
            if str(flag).strip()
        )
        unknown = flags - ALLOWED_INCLUDE_FLAGS
        if unknown:
            raise ValueError(
                f"include inválido: {', '.join(sorted(unknown))}. Use portfolio."
            )
        self.include_flags = flags

    @property
    def include_portfolio(self) -> bool:
        return "portfolio" in self.include_flags

    def has_name_filters(self) -> bool:
        return bool(self.customer_names) or bool(self.exclude_customer_names)

    def has_include_customer_filter(self) -> bool:
        return self.customer_codes is not None or self.customer_names is not None
