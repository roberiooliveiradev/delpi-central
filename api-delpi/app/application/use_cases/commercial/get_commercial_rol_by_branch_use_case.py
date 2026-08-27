"""Use case — ROL tabular por filial (01/02)."""

from __future__ import annotations

from typing import Any, Optional

from app.application.dto.commercial.get_rol_by_branch_request import GetRolByBranchRequest
from app.application.dto.financial.get_rol_request import GetRolRequest
from app.application.use_cases.commercial.commercial_analysis_payload_helpers import (
    branch_breakdown_rows,
)
from app.domain.ports.financial.financial_query_repository_port import (
    FinancialQueryRepositoryPort,
)

HEAD_OFFICE_BRANCH = "01"
BRANCH_OFFICE_BRANCH = "02"


def _to_iso_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    raw = str(value).strip()
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw


class GetCommercialRolByBranchUseCase:
    def __init__(
        self,
        *,
        financial_query_repository: FinancialQueryRepositoryPort,
    ) -> None:
        self._financial = financial_query_repository

    def execute(self, request: GetRolByBranchRequest) -> dict[str, Any]:
        start_iso = _to_iso_date(request.start_date)
        end_iso = _to_iso_date(request.end_date)
        filters = {
            "customer_segment": request.customer_segment,
            "customer_codes": request.customer_codes,
            "customer_names": request.customer_names,
            "exclude_customer_codes": request.exclude_customer_codes,
            "exclude_customer_names": request.exclude_customer_names,
        }
        rol_01 = self._financial.get_rol(
            GetRolRequest(
                branch=HEAD_OFFICE_BRANCH,
                start_date=start_iso,
                end_date=end_iso,
                **filters,
            )
        )
        rol_02 = self._financial.get_rol(
            GetRolRequest(
                branch=BRANCH_OFFICE_BRANCH,
                start_date=start_iso,
                end_date=end_iso,
                **filters,
            )
        )
        by_branch = {
            "branch_01": self._rol_metrics(rol_01),
            "branch_02": self._rol_metrics(rol_02),
        }
        items = branch_breakdown_rows(by_branch)
        return {
            "start_date": start_iso or request.start_date,
            "end_date": end_iso or request.end_date,
            "items": items,
            "summary": {
                "items_count": len(items),
                "total_rol": round(
                    sum(float(row.get("rol") or 0) for row in items),
                    2,
                ),
            },
        }

    @staticmethod
    def _rol_metrics(rol: dict[str, Any]) -> dict[str, float]:
        return {
            "rol": round(float(rol.get("rol") or 0), 2),
            "gross_revenue": round(float(rol.get("gross_revenue") or 0), 2),
            "returns": round(float(rol.get("returns") or 0), 2),
            "discounts": round(float(rol.get("discounts") or 0), 2),
        }
