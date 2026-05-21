# app/application/use_cases/lmp/list_lmp_dashboard_use_case.py
from dataclasses import asdict, replace
from datetime import date
from typing import Any, Dict, List, Optional

from si_app.application.dto.lmp.list_lmp_request import (
    DASHBOARD_STATUS_VALUES,
    LISTING_KIND_LMP,
    ListLMPRequest,
    resolve_dashboard_status_filter,
    resolve_listing_type_filter,
)
from si_app.application.services.lmp.lmp_dashboard_cache import (
    get_cached_lmp_dashboard,
    lmp_dashboard_cache_key,
    set_cached_lmp_dashboard,
)
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

    def _filter_items_by_status(
        self,
        items: List[LMPDashboardItem],
        status_filter: Optional[str],
    ) -> List[LMPDashboardItem]:
        if not status_filter:
            return items

        return [item for item in items if item.status == status_filter]

    @staticmethod
    def _parse_period_sort_key(value: Optional[str]) -> int:
        if not value or len(value) != 8:
            return 0
        try:
            return int(value)
        except ValueError:
            return 0

    @classmethod
    def _format_period_label(cls, value: Optional[str]) -> Optional[str]:
        sort_key = cls._parse_period_sort_key(value)
        if not sort_key:
            return None

        year = int(value[0:4])
        month = int(value[4:6])
        day = int(value[6:8])
        if not year or not month or not day:
            return None

        return date(year, month, day).strftime("%b %y")

    def _build_charts(self, items: List[LMPDashboardItem]) -> Dict[str, Any]:
        level_order = ["Nível 1", "Nível 2", "Nível 3"]

        level_data = [
            {"name": name, "value": sum(1 for item in items if item.nivel == name)}
            for name in level_order
        ]
        status_data = [
            {"name": name, "value": sum(1 for item in items if item.status == name)}
            for name in DASHBOARD_STATUS_VALUES
        ]

        lead_by_level = []
        for nivel in level_order:
            items_by_level = [
                item
                for item in items
                if item.nivel == nivel and item.lead_time_util is not None
            ]
            avg = (
                sum(item.lead_time_util or 0 for item in items_by_level)
                / len(items_by_level)
                if items_by_level
                else 0
            )
            lead_by_level.append(
                {"nivel": nivel, "valor": round(avg, 2)}
            )

        return {
            "levelData": level_data,
            "statusData": status_data,
            "leadByLevel": lead_by_level,
        }

    def execute(
        self,
        request: ListLMPRequest,
        status_filter: str = "Todos",
    ) -> Dict[str, Any]:
        resolved_status = resolve_dashboard_status_filter(status_filter)
        listing_type_key = resolve_listing_type_filter(request.listing_type) or "Todos"
        cache_key = lmp_dashboard_cache_key(
            date_start=request.date_start,
            date_end=request.date_end,
            branch=request.branch,
            listing_type=listing_type_key,
            status_filter=status_filter,
        )
        cached = get_cached_lmp_dashboard(cache_key)
        if cached is not None:
            return cached

        query_request = replace(request, include_qtd_pi=False)

        rows: List[LMP] = self._repository.list_lmps(query_request)
        enriched_all = [self._enrich_item(row) for row in rows]
        lmp_enriched = [
            item for item in enriched_all if item.listing_kind == LISTING_KIND_LMP
        ]
        enriched = self._filter_items_by_status(enriched_all, resolved_status)

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
            if lead_items
            else 0
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

        result = {
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
            "charts": self._build_charts(enriched),
        }
        set_cached_lmp_dashboard(cache_key, result)
        return result
