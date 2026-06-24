from app.application.dto.supplies.get_otd_request import GetOTDRequest
from app.application.services.supplies.supplies_otd_cache import (
    get_cached_supplies_otd,
    set_cached_supplies_otd,
    supplies_otd_cache_key,
)
from app.domain.ports.supplies.otd_query_repository_port import OtdQueryRepositoryPort


class GetOTDUseCase:

    def __init__(self, repository: OtdQueryRepositoryPort):
        self._repository = repository

    @staticmethod
    def _summary_from_monthly(
        monthly_breakdown: list[dict],
        request: GetOTDRequest,
    ) -> dict:
        branch_label = request.branch or "consolidated"

        if not monthly_breakdown:
            return {
                "branch": branch_label,
                "start_date": request.start_date or "",
                "end_date": request.end_date or "",
                "total_lines": 0,
                "on_time_lines": 0,
                "late_lines": 0,
                "otd_percentage": 0,
            }

        total_lines = sum(int(row.get("total_lines") or 0) for row in monthly_breakdown)
        on_time_lines = sum(int(row.get("on_time_lines") or 0) for row in monthly_breakdown)
        late_lines = sum(int(row.get("late_lines") or 0) for row in monthly_breakdown)

        month_dates = [
            str(row.get("month_date") or "").strip()
            for row in monthly_breakdown
            if row.get("month_date")
        ]
        start_date = min(month_dates) if month_dates else (request.start_date or "")
        end_date = max(month_dates) if month_dates else (request.end_date or "")

        otd_percentage = (
            round((on_time_lines * 100.0) / total_lines, 2)
            if total_lines > 0
            else 0
        )

        return {
            "branch": branch_label,
            "start_date": start_date,
            "end_date": end_date,
            "total_lines": total_lines,
            "on_time_lines": on_time_lines,
            "late_lines": late_lines,
            "otd_percentage": otd_percentage,
        }

    def _build_response(
        self,
        request: GetOTDRequest,
        *,
        monthly_breakdown: list[dict],
        top_late_suppliers: list[dict],
        late_deliveries: list[dict],
    ) -> dict:
        summary = self._summary_from_monthly(monthly_breakdown, request)

        total_lines = int(summary.get("total_lines") or 0)
        on_time_lines = int(summary.get("on_time_lines") or 0)
        late_lines = int(summary.get("late_lines") or 0)
        otd_percentage = float(summary.get("otd_percentage") or 0)

        late_percentage = (
            round((late_lines * 100.0 / total_lines), 2) if total_lines > 0 else 0
        )

        return {
            "branch": summary.get("branch") or request.branch or "consolidated",
            "start_date": summary.get("start_date") or request.start_date or "",
            "end_date": summary.get("end_date") or request.end_date or "",
            "summary": {
                "total_lines": total_lines,
                "on_time_lines": on_time_lines,
                "late_lines": late_lines,
                "otd_percentage": otd_percentage,
                "late_percentage": late_percentage,
            },
            "monthly_breakdown": monthly_breakdown,
            "top_late_suppliers": top_late_suppliers,
            "late_deliveries": late_deliveries,
        }

    def execute(self, request: GetOTDRequest) -> dict:
        cache_key = supplies_otd_cache_key(request)
        cached = get_cached_supplies_otd(cache_key)
        if cached is not None:
            return cached

        monthly_breakdown = self._repository.get_otd_monthly_breakdown(request)
        top_late_suppliers = self._repository.get_top_late_suppliers(request)
        late_deliveries = self._repository.get_late_deliveries(request)

        result = self._build_response(
            request,
            monthly_breakdown=monthly_breakdown,
            top_late_suppliers=top_late_suppliers,
            late_deliveries=late_deliveries,
        )
        set_cached_supplies_otd(cache_key, result)
        return result
