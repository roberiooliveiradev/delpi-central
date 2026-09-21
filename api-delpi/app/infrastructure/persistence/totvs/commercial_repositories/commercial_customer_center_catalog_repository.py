"""Distinct customer centers from the SA7 product–customer link."""

from __future__ import annotations

from typing import Optional

from app.domain.services.commercial_customer_codes_filter_service import (
    CommercialCustomerCodesFilterService,
)
from app.domain.totvs.protheus_customer_center import (
    customer_center_catalog_label,
    customer_center_catalog_sql,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


class CommercialCustomerCenterCatalogRepository(BaseRepository):
    def list_centers(
        self,
        customer_codes: Optional[list[str]] = None,
    ) -> list[dict[str, str]]:
        qb = QueryBuilder()
        if customer_codes is not None:
            CommercialCustomerCodesFilterService.apply_to_query_builder(
                qb,
                "RTRIM(LTRIM(A7.A7_CLIENTE))",
                customer_codes,
            )
        else:
            qb.raw("1 = 1")
        where_sql, params = qb.build()
        sql = customer_center_catalog_sql(customer_code_filter_sql=where_sql)
        with self as repo:
            rows = repo.execute_query(sql, params) or []
        items: list[dict[str, str]] = []
        for row in rows:
            center = str(row.get("center") or "").strip()
            if not center:
                continue
            short_name = str(row.get("short_name") or "").strip() or None
            items.append(
                {
                    "center": center,
                    "label": customer_center_catalog_label(center, short_name),
                }
            )
        return items
