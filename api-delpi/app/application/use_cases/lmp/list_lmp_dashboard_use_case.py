# app/application/use_cases/lmp/list_lmp_dashboard_use_case.py
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

    def _build_base_cache_key(
        self,
        request: ListLMPRequest,
        status_filter: str,
    ) -> str:
        listing_type_key = resolve_listing_type_filter(request.listing_type) or "Todos"
        return lmp_dashboard_cache_key(
            date_start=request.date_start,
            date_end=request.date_end,
            branch=request.branch,
            listing_type=listing_type_key,
            status_filter=status_filter,
        )

    def _load_enriched(
        self,
        request: ListLMPRequest,
        status_filter: str,
    ) -> tuple[List[LMPDashboardItem], List[LMPDashboardItem], List[LMPDashboardItem]]:
        """Carrega, enriquece e filtra as LMPs. Retorna (all, lmp_only, filtered)."""
        base_key = self._build_base_cache_key(request, status_filter) + "|enriched"
        cached = get_cached_lmp_dashboard(base_key)
        if cached is not None:
            return cached["all"], cached["lmp_only"], cached["filtered"]

        resolved_status = resolve_dashboard_status_filter(status_filter)
        query_request = replace(request, include_qtd_pi=False)

        rows: List[LMP] = self._repository.list_lmps(query_request)
        enriched_all = [self._enrich_item(row) for row in rows]
        lmp_enriched = [
            item for item in enriched_all if item.listing_kind == LISTING_KIND_LMP
        ]
        filtered = self._filter_items_by_status(enriched_all, resolved_status)

        set_cached_lmp_dashboard(base_key, {
            "all": enriched_all,
            "lmp_only": lmp_enriched,
            "filtered": filtered,
        })
        return enriched_all, lmp_enriched, filtered

    def _compute_summary(
        self,
        lmp_enriched: List[LMPDashboardItem],
        total_items: int,
    ) -> Dict[str, Any]:
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

        return {
            "total_lmps": total_lmps_for_kpi,
            "total_items": total_items,
            "percent_dentro_prazo": round(percent_dentro_prazo, 2),
            "avg_lead_time": round(avg_lead_time, 2),
        }

    def _load_summary_rows(
        self,
        request: ListLMPRequest,
    ) -> List[LMPDashboardItem]:
        """Carrega apenas os campos necessários para KPIs via query leve."""
        cache_key = self._build_base_cache_key(request, "Todos") + "|summary-rows"
        cached = get_cached_lmp_dashboard(cache_key)
        if cached is not None:
            return cached

        query_request = replace(request, include_qtd_pi=False)
        raw_rows = self._repository.get_lmp_dashboard_summary(query_request)
        items = []
        for row in raw_rows:
            nivel, sla_days, sla_minutes, data_limite, lead_time_util, status = (
                LMPBusinessRules.get_dashboard_status(
                    start_date_str=row.get("start_date"),
                    end_date_str=row.get("end_date"),
                    qtd_pi=row.get("qtd_pi"),
                    engineering_status=row.get("engineering_status"),
                    engineering_total_minutes=row.get("engineering_total_minutes"),
                )
            )
            items.append(LMPDashboardItem(
                branch=row.get("branch"),
                sale_number=row.get("sale_number"),
                sale_description=row.get("sale_description") or "",
                listing_kind=row.get("listing_kind"),
                start_date=row.get("start_date"),
                end_date=row.get("end_date"),
                engineering_status=row.get("engineering_status"),
                qtd_pi=int(row.get("qtd_pi") or 0),
                nivel=nivel,
                dias_uteis_sla=sla_days,
                sla_minutos=sla_minutes,
                engineering_total_minutes=int(row.get("engineering_total_minutes") or 0),
                data_limite=data_limite,
                lead_time_util=lead_time_util,
                status=status,
            ))

        set_cached_lmp_dashboard(cache_key, items)
        return items

    def execute_summary(
        self,
        request: ListLMPRequest,
        status_filter: str = "Todos",
    ) -> Dict[str, Any]:
        """Fase 1: apenas KPIs (summary) — usa query leve sem carregar items completos."""
        items = self._load_summary_rows(request)
        lmp_only = [i for i in items if i.listing_kind == LISTING_KIND_LMP]

        resolved_status = resolve_dashboard_status_filter(status_filter)
        filtered = self._filter_items_by_status(items, resolved_status)

        return self._compute_summary(lmp_only, len(filtered))

    def execute_charts(
        self,
        request: ListLMPRequest,
        status_filter: str = "Todos",
    ) -> Dict[str, Any]:
        """Fase 2: dados dos gráficos — reutiliza summary rows (query leve)."""
        items = self._load_summary_rows(request)
        resolved_status = resolve_dashboard_status_filter(status_filter)
        filtered = self._filter_items_by_status(items, resolved_status)
        return self._build_charts(filtered)

    def execute_items(
        self,
        request: ListLMPRequest,
        status_filter: str = "Todos",
    ) -> Dict[str, Any]:
        """Fase 3: itens paginados — reutiliza summary rows (query leve, cacheada)."""
        items = self._load_summary_rows(request)
        resolved_status = resolve_dashboard_status_filter(status_filter)
        filtered = self._filter_items_by_status(items, resolved_status)
        total = len(filtered)

        page = request.page or 1
        page_size = request.page_size or DEFAULT_DASHBOARD_PAGE_SIZE
        start = (page - 1) * page_size
        end = start + page_size
        paginated = filtered[start:end]

        return {
            "items": [asdict(item) for item in paginated],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def execute(
        self,
        request: ListLMPRequest,
        status_filter: str = "Todos",
        *,
        scope: str | None = None,
    ) -> Dict[str, Any]:
        del scope

        page = request.page or 1
        page_size = request.page_size or DEFAULT_DASHBOARD_PAGE_SIZE

        cache_key = "|".join([
            self._build_base_cache_key(request, status_filter),
            f"page={page}",
            f"size={page_size}",
        ])
        cached = get_cached_lmp_dashboard(cache_key)
        if cached is not None:
            return cached

        _, lmp_enriched, filtered = self._load_enriched(request, status_filter)
        total = len(filtered)

        start = (page - 1) * page_size
        end = start + page_size
        paginated = filtered[start:end]

        result = {
            "items": [asdict(item) for item in paginated],
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": self._compute_summary(lmp_enriched, total),
            "charts": self._build_charts(filtered),
        }
        set_cached_lmp_dashboard(cache_key, result)
        return result
