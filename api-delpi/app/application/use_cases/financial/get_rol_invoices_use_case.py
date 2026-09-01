from __future__ import annotations

from typing import Any

from app.application.dto.financial.get_rol_request import GetRolRequest
from app.domain.ports.financial.financial_query_repository_port import (
    FinancialQueryRepositoryPort,
)

DEFAULT_ROL_INVOICE_LIMIT = 8000


class GetRolInvoicesUseCase:
    """Lista notas (SD2) e devoluções (SD1) que entram no ROL do período."""

    def __init__(self, repository: FinancialQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: GetRolRequest, *, limit: int | None = None) -> dict:
        resolved_limit = self._resolve_limit(limit)
        rows = self._repository.list_rol_invoices(request, limit=resolved_limit)
        truncated = len(rows) > resolved_limit
        items = [self._map_row(row) for row in rows[:resolved_limit]]
        return {
            "branch": request.branch or "consolidated",
            "start_date": request.start_date or "",
            "end_date": request.end_date or "",
            "items": items,
            "truncated": truncated,
            "totals": {
                "count": len(items),
                "gross": round(sum(item["gross"] for item in items), 2),
                "discounts": round(sum(item["discounts"] for item in items), 2),
                "returns": round(sum(item["returns"] for item in items), 2),
                "taxes": round(sum(item["taxes"] for item in items), 2),
                "rol": round(sum(item["rol"] for item in items), 2),
            },
            "pagination": {
                "limit": resolved_limit,
                "offset": 0,
                "returned": len(items),
                "is_complete": not truncated,
            },
        }

    @staticmethod
    def _resolve_limit(raw: int | None) -> int:
        try:
            value = int(raw) if raw is not None else DEFAULT_ROL_INVOICE_LIMIT
        except (TypeError, ValueError):
            value = DEFAULT_ROL_INVOICE_LIMIT
        return min(max(value, 1), DEFAULT_ROL_INVOICE_LIMIT)

    @classmethod
    def _map_row(cls, row: dict[str, Any]) -> dict[str, Any]:
        kind = str(row.get("kind") or "").strip().lower()
        if kind not in {"sale", "return"}:
            kind = "sale"
        return {
            "kind": kind,
            "branch": str(row.get("branch") or "").strip(),
            "issue_date": cls._iso_date(row.get("issue_date")),
            "invoice_number": str(row.get("invoice_number") or "").strip(),
            "series": str(row.get("series") or "").strip(),
            "customer_code": str(row.get("customer_code") or "").strip(),
            "customer_store": str(row.get("customer_store") or "").strip(),
            "customer_name": str(row.get("customer_name") or "").strip(),
            "gross": cls._as_float(row.get("gross")),
            "discounts": cls._as_float(row.get("discounts")),
            "returns": cls._as_float(row.get("returns")),
            "taxes": cls._as_float(row.get("taxes")),
            "rol": cls._as_float(row.get("rol")),
        }

    @staticmethod
    def _as_float(value: Any) -> float:
        if value is None or value == "":
            return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _iso_date(raw: Any) -> str:
        text = str(raw or "").strip()
        if len(text) >= 10 and text[4] == "-" and text[7] == "-":
            return text[:10]
        digits = "".join(ch for ch in text if ch.isdigit())
        if len(digits) >= 8:
            return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"
        return text
