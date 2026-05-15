from si_app.application.dto.supplies.get_otd_request import GetOTDRequest
from si_app.domain.ports.supplies.otd_query_repository_port import OtdQueryRepositoryPort


class GetOTDUseCase:

    def __init__(self, repository: OtdQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: GetOTDRequest) -> dict:
        summary = self._repository.get_otd_summary(request)
        monthly_breakdown = self._repository.get_otd_monthly_breakdown(request)
        top_late_suppliers = self._repository.get_top_late_suppliers(request)
        late_deliveries = self._repository.get_late_deliveries(request)

        total_lines = int(summary.get("total_lines") or 0)
        on_time_lines = int(summary.get("on_time_lines") or 0)
        late_lines = int(summary.get("late_lines") or 0)
        otd_percentage = float(summary.get("otd_percentage") or 0)

        late_percentage = round((late_lines * 100.0 / total_lines), 2) if total_lines > 0 else 0

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