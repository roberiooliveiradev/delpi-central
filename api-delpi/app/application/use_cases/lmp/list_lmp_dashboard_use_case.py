# app/application/use_cases/lmp/list_lmp_dashboard_use_case.py
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from datetime import date
from typing import Any, Dict, List, Optional

from app.application.dto.lmp.list_lmp_request import (
    DASHBOARD_STATUS_VALUES,
    LISTING_KIND_LMP,
    ListLMPRequest,
    resolve_dashboard_status_filter,
    resolve_listing_type_filter,
)
from app.application.services.lmp.lmp_dashboard_cache import (
    get_cached_lmp_dashboard,
    lmp_dashboard_cache_key,
    set_cached_lmp_dashboard,
)
from app.application.dto.lmp.lmp_dashboard_item import LMPDashboardItem
from app.application.services.lmp_business_rules import LMPBusinessRules
from app.domain.entities.lmp.lmp import LMP
from app.domain.ports.lmp.lmp_query_repository_port import LMPQueryRepositoryPort

DEFAULT_DASHBOARD_PAGE_SIZE = 50
DASHBOARD_SCOPE_AGGREGATES = "aggregates"
DASHBOARD_SCOPE_ITEMS = "items"
DASHBOARD_SCOPE_FULL = "full"


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

    def _enrich_summary_row(self, row: dict) -> LMPDashboardItem:
        return self._enrich_item(
            LMP(
                branch=row.get("branch"),
                sale_number=row.get("sale_number") or "",
                sale_description="",
                listing_kind=row.get("listing_kind"),
                start_date=row.get("start_date"),
                end_date=row.get("end_date"),
                engineering_status=row.get("engineering_status"),
                engineering_total_minutes=row.get("engineering_total_minutes"),
                qtd_pi=row.get("qtd_pi"),
            )
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

    def _build_summary_metrics(
        self,
        enriched_all: List[LMPDashboardItem],
        *,
        status_filter: Optional[str],
    ) -> tuple[dict[str, Any], List[LMPDashboardItem]]:
        filtered = self._filter_items_by_status(enriched_all, status_filter)
        lmp_enriched = [
            item for item in filtered if item.listing_kind == LISTING_KIND_LMP
        ]

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

        summary = {
            "total_lmps": total_lmps_for_kpi,
            "total_items": len(filtered),
            "percent_dentro_prazo": round(percent_dentro_prazo, 2),
            "avg_lead_time": round(avg_lead_time, 2),
        }
        return summary, filtered

    def _load_enriched_aggregates(
        self,
        request: ListLMPRequest,
    ) -> List[LMPDashboardItem]:
        query_request = replace(request, include_qtd_pi=False)
        summary_rows = self._repository.get_lmp_dashboard_summary(query_request)
        return [self._enrich_summary_row(row) for row in summary_rows]

    def _execute_aggregates(
        self,
        request: ListLMPRequest,
        *,
        resolved_status: Optional[str],
    ) -> Dict[str, Any]:
        enriched_all = self._load_enriched_aggregates(request)
        summary, filtered = self._build_summary_metrics(
            enriched_all,
            status_filter=resolved_status,
        )

        return {
            "items": [],
            "total": len(filtered),
            "page": 1,
            "page_size": 0,
            "summary": summary,
            "charts": self._build_charts(filtered),
        }

    def _execute_items(
        self,
        request: ListLMPRequest,
        *,
        resolved_status: Optional[str],
        page: int,
        page_size: int,
    ) -> Dict[str, Any]:
        query_request = replace(request, include_qtd_pi=False)
        page_result = self._repository.list_lmps_page(
            replace(
                query_request,
                page=page,
                page_size=page_size,
            )
        )
        enriched_page = [
            self._enrich_item(row) for row in page_result.items
        ]
        filtered_page = self._filter_items_by_status(
            enriched_page,
            resolved_status,
        )

        return {
            "items": [asdict(item) for item in filtered_page],
            "total": page_result.total,
            "page": page_result.page,
            "page_size": page_result.page_size,
            "summary": None,
            "charts": None,
        }

    def _execute_full(
        self,
        request: ListLMPRequest,
        *,
        resolved_status: Optional[str],
        page: int,
        page_size: int,
    ) -> Dict[str, Any]:
        query_request = replace(request, include_qtd_pi=False)
        page_request = replace(
            query_request,
            page=page,
            page_size=page_size,
        )

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_summary = executor.submit(
                self._repository.get_lmp_dashboard_summary,
                query_request,
            )
            future_page = executor.submit(
                self._repository.list_lmps_page,
                page_request,
            )
            summary_rows = future_summary.result()
            page_result = future_page.result()

        enriched_all = [self._enrich_summary_row(row) for row in summary_rows]
        summary, filtered = self._build_summary_metrics(
            enriched_all,
            status_filter=resolved_status,
        )

        enriched_page = [self._enrich_item(row) for row in page_result.items]
        filtered_page = self._filter_items_by_status(
            enriched_page,
            resolved_status,
        )

        return {
            "items": [asdict(item) for item in filtered_page],
            "total": len(filtered),
            "page": page_result.page,
            "page_size": page_result.page_size,
            "summary": summary,
            "charts": self._build_charts(filtered),
        }

    def execute(
        self,
        request: ListLMPRequest,
        status_filter: str = "Todos",
        *,
        scope: str | None = None,
    ) -> Dict[str, Any]:
        resolved_status = resolve_dashboard_status_filter(status_filter)
        listing_type_key = resolve_listing_type_filter(request.listing_type) or "Todos"
        normalized_scope = (scope or DASHBOARD_SCOPE_FULL).strip().lower()

        page = request.page or 1
        page_size = request.page_size or DEFAULT_DASHBOARD_PAGE_SIZE

        cache_key = lmp_dashboard_cache_key(
            date_start=request.date_start,
            date_end=request.date_end,
            branch=request.branch,
            listing_type=listing_type_key,
            status_filter=status_filter,
        )
        cache_key = f"{cache_key}|scope={normalized_scope}|page={page}|size={page_size}"

        cached = get_cached_lmp_dashboard(cache_key)
        if cached is not None:
            return cached

        if normalized_scope == DASHBOARD_SCOPE_AGGREGATES:
            result = self._execute_aggregates(
                request,
                resolved_status=resolved_status,
            )
        elif normalized_scope == DASHBOARD_SCOPE_ITEMS:
            result = self._execute_items(
                request,
                resolved_status=resolved_status,
                page=page,
                page_size=page_size,
            )
        else:
            result = self._execute_full(
                request,
                resolved_status=resolved_status,
                page=page,
                page_size=page_size,
            )

        set_cached_lmp_dashboard(cache_key, result)
        return result
