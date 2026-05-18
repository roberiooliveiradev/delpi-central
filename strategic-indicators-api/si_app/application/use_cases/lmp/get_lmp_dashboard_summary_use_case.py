from si_app.application.dto.lmp.list_lmp_request import ListLMPRequest
from si_app.application.dto.lmp.lmp_dashboard_summary_response import (
    LMPDashboardSummaryResponse,
)
from si_app.application.services.lmp.lmp_dashboard_summary_cache import (
    get_cached_lmp_dashboard_summary,
    lmp_dashboard_summary_cache_key,
    set_cached_lmp_dashboard_summary,
)
from si_app.application.services.lmp_business_rules import LMPBusinessRules
from si_app.domain.ports.lmp.lmp_query_repository_port import LMPQueryRepositoryPort


class GetLMPDashboardSummaryUseCase:
    def __init__(self, repository: LMPQueryRepositoryPort):
        self._repository = repository

    def execute(
        self,
        request: ListLMPRequest,
        *,
        include_avg_lead_time: bool = True,
    ) -> LMPDashboardSummaryResponse:
        cache_key = lmp_dashboard_summary_cache_key(
            date_start=request.date_start,
            date_end=request.date_end,
            branch=request.branch,
            include_avg_lead_time=include_avg_lead_time,
        )
        cached = get_cached_lmp_dashboard_summary(cache_key)
        if cached is not None:
            return cached

        rows = self._repository.get_lmp_dashboard_summary(request)

        total_lmps = len(rows)
        total_dentro_prazo = 0
        lead_times: list[int] = []

        for row in rows:
            if include_avg_lead_time:
                _, _, _, _, lead_time_util, status = LMPBusinessRules.get_dashboard_status(
                    start_date_str=row.get("start_date"),
                    end_date_str=row.get("end_date"),
                    qtd_pi=row.get("qtd_pi"),
                    engineering_status=row.get("engineering_status"),
                    engineering_total_minutes=row.get("engineering_total_minutes"),
                )
                if lead_time_util is not None:
                    lead_times.append(lead_time_util)
            else:
                status = LMPBusinessRules.resolve_dashboard_status(
                    start_date_str=row.get("start_date"),
                    end_date_str=row.get("end_date"),
                    qtd_pi=row.get("qtd_pi"),
                    engineering_status=row.get("engineering_status"),
                    engineering_total_minutes=row.get("engineering_total_minutes"),
                )

            if status != LMPBusinessRules.DASHBOARD_STATUS_LATE:
                total_dentro_prazo += 1

        percent_dentro_prazo = (
            round((total_dentro_prazo / total_lmps) * 100, 2)
            if total_lmps > 0
            else 0.0
        )

        avg_lead_time = (
            round(sum(lead_times) / len(lead_times), 2)
            if include_avg_lead_time and lead_times
            else 0.0
        )

        response = LMPDashboardSummaryResponse(
            total_lmps=total_lmps,
            percent_dentro_prazo=percent_dentro_prazo,
            avg_lead_time=avg_lead_time,
        )
        set_cached_lmp_dashboard_summary(cache_key, response)
        return response
