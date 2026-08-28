"""Use case — ROL realizado (scalar) para hub summary + meta SI."""

from __future__ import annotations

from typing import Any, Optional

from app.application.dto.financial.get_rol_request import GetRolRequest
from app.domain.ports.financial.financial_query_repository_port import (
    FinancialQueryRepositoryPort,
)
from app.domain.totvs.protheus_branches import optional_concrete_branch


def _to_iso_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    raw = str(value).strip()
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw


class GetCommercialRolSummaryUseCase:
    def __init__(
        self,
        *,
        financial_query_repository: FinancialQueryRepositoryPort,
    ) -> None:
        self._financial = financial_query_repository

    def execute(
        self,
        *,
        branch: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        customer_segment: Optional[str] = None,
        customer_codes: Optional[list[str]] = None,
        customer_names: Optional[list[str]] = None,
        exclude_customer_codes: Optional[list[str]] = None,
        exclude_customer_names: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        start_iso = _to_iso_date(start_date)
        end_iso = _to_iso_date(end_date)
        concrete_branch = optional_concrete_branch(branch)
        rol = self._financial.get_rol(
            GetRolRequest(
                branch=concrete_branch,
                start_date=start_iso,
                end_date=end_iso,
                customer_segment=customer_segment,
                customer_codes=customer_codes,
                customer_names=customer_names,
                exclude_customer_codes=exclude_customer_codes,
                exclude_customer_names=exclude_customer_names,
            )
        )
        return {
            "branch": concrete_branch,
            "start_date": start_iso or start_date,
            "end_date": end_iso or end_date,
            "rol": round(float(rol.get("rol") or 0), 2),
            "gross_revenue": round(float(rol.get("gross_revenue") or 0), 2),
            "returns": round(float(rol.get("returns") or 0), 2),
            "discounts": round(float(rol.get("discounts") or 0), 2),
        }
