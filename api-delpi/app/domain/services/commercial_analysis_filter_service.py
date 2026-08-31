from __future__ import annotations

from typing import Optional

from app.domain.services.commercial_analysis_filter_request import (
    ALLOWED_INCLUDE_FLAGS,
    CommercialAnalysisFilterRequest,
)
from app.domain.services.commercial_customer_code_store_filter_service import (
    CommercialCustomerCodeStoreFilterService,
)
from app.domain.services.commercial_customer_codes_filter_service import (
    CommercialCustomerCodesFilterService,
)
from app.domain.services.commercial_customer_name_filter_service import (
    CommercialCustomerNameFilterService,
)
from app.domain.services.commercial_customer_segment_service import (
    CommercialCustomerSegmentService,
)


class CommercialAnalysisFilterService:
    """Compose segment → include (codes ∪ names) → exclude (codes ∪ names)."""

    @staticmethod
    def parse_include_flags(value: Optional[str]) -> frozenset[str]:
        if value is None or not str(value).strip():
            return frozenset()
        flags = {
            part.strip().lower()
            for part in str(value).split(",")
            if part.strip()
        }
        unknown = flags - ALLOWED_INCLUDE_FLAGS
        if unknown:
            raise ValueError(
                f"include inválido: {', '.join(sorted(unknown))}. Use portfolio."
            )
        return frozenset(flags)

    @staticmethod
    def normalize_customer_names(
        value: Optional[str] | Optional[list[str]],
    ) -> Optional[list[str]]:
        return CommercialCustomerNameFilterService.normalize(value)

    @classmethod
    def apply_to_query_builder(
        cls,
        qb,
        *,
        customer_code_column: str,
        customer_name_column: Optional[str] = None,
        customer_store_column: Optional[str] = None,
        customer_segment: Optional[str] = None,
        customer_codes: Optional[list[str]] = None,
        customer_code_stores: Optional[list[tuple[str, str]]] = None,
        customer_names: Optional[list[str]] = None,
        exclude_customer_codes: Optional[list[str]] = None,
        exclude_customer_names: Optional[list[str]] = None,
    ) -> None:
        CommercialCustomerSegmentService.apply_segment_to_query_builder(
            qb,
            customer_code_column,
            customer_segment,
        )
        cls._apply_include(
            qb,
            customer_code_column=customer_code_column,
            customer_name_column=customer_name_column,
            customer_codes=customer_codes,
            customer_names=customer_names,
        )
        if customer_store_column:
            CommercialCustomerCodeStoreFilterService.apply_to_query_builder(
                qb,
                customer_code_column,
                customer_store_column,
                customer_code_stores,
            )
        CommercialCustomerCodesFilterService.apply_exclude_to_query_builder(
            qb,
            customer_code_column,
            exclude_customer_codes,
        )
        if customer_name_column:
            CommercialCustomerNameFilterService.apply_exclude_to_query_builder(
                qb,
                customer_name_column,
                exclude_customer_names,
            )

    @classmethod
    def apply_from_request(
        cls,
        qb,
        request: CommercialAnalysisFilterRequest,
        *,
        customer_code_column: str,
        customer_name_column: Optional[str] = None,
        customer_store_column: Optional[str] = None,
    ) -> None:
        cls.apply_to_query_builder(
            qb,
            customer_code_column=customer_code_column,
            customer_name_column=customer_name_column,
            customer_store_column=customer_store_column,
            customer_segment=request.customer_segment,
            customer_codes=request.customer_codes,
            customer_code_stores=request.customer_code_stores,
            customer_names=request.customer_names,
            exclude_customer_codes=request.exclude_customer_codes,
            exclude_customer_names=request.exclude_customer_names,
        )

    @staticmethod
    def _apply_include(
        qb,
        *,
        customer_code_column: str,
        customer_name_column: Optional[str],
        customer_codes: Optional[list[str]],
        customer_names: Optional[list[str]],
    ) -> None:
        has_codes = customer_codes is not None
        has_names = customer_names is not None and bool(customer_name_column)

        if not has_codes and not has_names:
            return

        if has_codes and not has_names:
            CommercialCustomerCodesFilterService.apply_to_query_builder(
                qb,
                customer_code_column,
                customer_codes,
            )
            return

        if has_names and not has_codes:
            CommercialCustomerNameFilterService.apply_include_to_query_builder(
                qb,
                customer_name_column,  # type: ignore[arg-type]
                customer_names,
            )
            return

        # codes + names → (code IN) OR (name LIKE …)
        code_list = list(customer_codes or [])
        name_list = list(customer_names or [])
        if not code_list and not name_list:
            qb.raw("1 = 0")
            return

        parts: list[str] = []
        params: list[str] = []
        if code_list:
            placeholders = ",".join("?" for _ in code_list)
            parts.append(f"{customer_code_column.strip()} IN ({placeholders})")
            params.extend(code_list)
        if name_list and customer_name_column:
            name_parts: list[str] = []
            for name in name_list:
                name_parts.append(
                    f"LOWER(ISNULL({customer_name_column.strip()}, '')) LIKE ?"
                )
                params.append(f"%{name.casefold()}%")
            parts.append(f"({' OR '.join(name_parts)})")
        qb.raw(f"({' OR '.join(parts)})", *params)
