from __future__ import annotations

from datetime import date

from app.application.dto.audit_5s.audit_5s_dashboard_response import (
    Audit5sDashboardCharts,
    Audit5sDashboardItem,
    Audit5sDashboardPagination,
    Audit5sDashboardResponse,
    Audit5sDashboardSummary,
)
from app.application.dto.audit_5s.get_audit_5s_dashboard_request import (
    GetAudit5sDashboardRequest,
)
from app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository import (
    PostgresAudit5sRepository,
)


VALID_BRANCHES = ("01", "02")
VALID_SHIFTS = ("TURNO_1", "TURNO_2", "TURNO_3", "ADMINISTRATIVO")
VALID_STATUSES = ("draft", "evaluation_complete", "nc_in_progress", "closed")
VALID_GRANULARITIES = ("day", "week", "month")
MAX_DATE_RANGE_DAYS = 366
MAX_PAGE_SIZE = 100


class GetAudit5sDashboardUseCase:
    def __init__(self, repository: PostgresAudit5sRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        branch_code: str,
        date_start: str,
        date_end: str,
        area_id: str | None = None,
        shift: str | None = None,
        audit_status: str | None = None,
        senso_order: int | None = None,
        granularity: str = "month",
        page: int = 1,
        page_size: int = 20,
    ) -> Audit5sDashboardResponse:
        if branch_code not in VALID_BRANCHES:
            raise ValueError("branch inválida. Use 01 ou 02.")

        parsed_start = self._parse_date(date_start)
        parsed_end = self._parse_date(date_end)
        if parsed_start is None or parsed_end is None:
            raise ValueError("Datas inválidas. Use o formato YYYY-MM-DD.")
        if parsed_end < parsed_start:
            raise ValueError("date_end deve ser maior ou igual a date_start.")
        if (parsed_end - parsed_start).days > MAX_DATE_RANGE_DAYS:
            raise ValueError(f"Intervalo máximo permitido: {MAX_DATE_RANGE_DAYS} dias.")

        if shift and shift not in VALID_SHIFTS:
            raise ValueError("Turno inválido.")
        if audit_status and audit_status not in VALID_STATUSES:
            raise ValueError("Status de auditoria inválido.")
        if granularity not in VALID_GRANULARITIES:
            raise ValueError("granularity inválida. Use day, week ou month.")
        if senso_order is not None and senso_order not in range(1, 6):
            raise ValueError("senso_order inválido. Use um valor entre 1 e 5.")

        resolved_page = max(page, 1)
        resolved_page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

        request = GetAudit5sDashboardRequest(
            branch_code=branch_code,
            date_start=parsed_start,
            date_end=parsed_end,
            area_id=area_id.strip() if area_id and area_id.strip() else None,
            shift=shift,
            audit_status=audit_status,
            senso_order=senso_order,
            granularity=granularity,
            page=resolved_page,
            page_size=resolved_page_size,
        )
        data = self._repository.get_dashboard(request)
        return Audit5sDashboardResponse(
            summary=Audit5sDashboardSummary(**data["summary"]),
            charts=Audit5sDashboardCharts(**data["charts"]),
            items=[Audit5sDashboardItem(**item) for item in data["items"]],
            pagination=Audit5sDashboardPagination(**data["pagination"]),
        )

    @staticmethod
    def _parse_date(value: str) -> date | None:
        try:
            return date.fromisoformat(str(value).strip()[:10])
        except ValueError:
            return None
