# app/application/use_cases/lmp/list_lmp_dashboard_use_case.py
from dataclasses import asdict, replace
from typing import List, Dict, Any

from si_app.application.dto.lmp.list_lmp_request import ListLMPRequest
from si_app.application.dto.lmp.lmp_dashboard_item import LMPDashboardItem
from si_app.application.services.lmp_business_rules import LMPBusinessRules
from si_app.domain.entities.lmp.lmp import LMP
from si_app.domain.ports.lmp.lmp_query_repository_port import LMPQueryRepositoryPort


class ListLMPDashboardUseCase:

    def __init__(self, repository: LMPQueryRepositoryPort):
        self._repository = repository

    def _enrich_item(self, item: LMP) -> LMPDashboardItem:
        nivel, sla_days, sla_minutes, data_limite, lead_time_util, status = (
            LMPBusinessRules.get_dashboard_status(
                start_date_str=item.start_date,
                end_date_str=item.end_date,
                qtd_pi=item.qtd_pi,
                engineering_status=item.engineering_status,
                engineering_total_minutes=item.engineering_total_minutes,
            )
        )

        return LMPDashboardItem(
            branch=item.branch,
            sale_number=item.sale_number,
            sale_description=item.sale_description,
            listing_kind=item.listing_kind,
            start_date=item.start_date,
            end_date=item.end_date,
            engineering_status=item.engineering_status,
            qtd_pi=int(item.qtd_pi or 0),
            nivel=nivel,
            dias_uteis_sla=sla_days,
            sla_minutos=sla_minutes,
            engineering_total_minutes=int(item.engineering_total_minutes or 0),
            data_limite=data_limite,
            lead_time_util=lead_time_util,
            status=status,
        )

    def execute(self, request: ListLMPRequest, status_filter: str = "Todos") -> Dict[str, Any]:
        rows: List[LMP] = self._repository.list_lmps(request)
        lmp_summary_request = replace(request, listing_type="lmp")
        lmp_rows: List[LMP] = self._repository.list_lmps(lmp_summary_request)

        enriched = [self._enrich_item(row) for row in rows]
        lmp_enriched = [self._enrich_item(row) for row in lmp_rows]

        if status_filter != "Todos":
            enriched = [item for item in enriched if item.status == status_filter]

        total = len(enriched)

        lead_items = [
            item for item in lmp_enriched if item.lead_time_util is not None
        ]
        pontuais = len(
            [item for item in lmp_enriched if item.status != "Atrasado"]
        )
        total_lmps_for_kpi = len(lmp_enriched)

        percent_dentro_prazo = (
            (pontuais / total_lmps_for_kpi * 100) if total_lmps_for_kpi else 0
        )
        avg_lead_time = (
            sum(item.lead_time_util or 0 for item in lead_items) / len(lead_items)
            if lead_items else 0
        )

        if not request.page_size:
            paginated = enriched
            page = 1
            page_size = total
        else:
            page = request.page or 1
            start = (page - 1) * request.page_size
            end = start + request.page_size
            paginated = enriched[start:end]
            page_size = request.page_size

        return {
            "items": [asdict(item) for item in paginated],
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": {
                "total_lmps": total_lmps_for_kpi,
                "total_items": total,
                "percent_dentro_prazo": round(percent_dentro_prazo, 2),
                "avg_lead_time": round(avg_lead_time, 2),
            },
        }
