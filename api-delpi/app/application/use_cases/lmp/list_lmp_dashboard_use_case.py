# app/application/use_cases/lmp/list_lmp_dashboard_use_case.py
from dataclasses import asdict, fields, replace
from typing import Any, Dict, List, Literal, Optional

from app.application.dto.lmp.list_lmp_request import (
    DASHBOARD_STATUS_VALUES,
    LISTING_KIND_LMP,
    ListLMPRequest,
    resolve_dashboard_status_filter,
    resolve_listing_type_filter,
)
from app.application.services.lmp.lmp_dashboard_cache import (
    get_cached_lmp_dashboard,
    get_or_set_cached_lmp_dashboard,
    lmp_dashboard_cache_key,
    set_cached_lmp_dashboard,
)
from app.application.dto.lmp.lmp_dashboard_item import LMPDashboardItem
from app.application.services.lmp_business_rules import LMPBusinessRules
from app.domain.entities.lmp.lmp import LMP
from app.domain.ports.lmp.lmp_query_repository_port import LMPQueryRepositoryPort

DEFAULT_DASHBOARD_PAGE_SIZE = 50
SummaryLoadMode = Literal["kpi", "full"]
_SUMMARY_ROWS_CACHE_SUFFIX_KPI = "|summary-rows|kpi"
_SUMMARY_ROWS_CACHE_SUFFIX_FULL = "|summary-rows|pi1"


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
            nivel=nivel,
            dias_uteis_sla=sla_days,
            sla_minutos=sla_minutes,
            engineering_total_minutes=int(item.engineering_total_minutes or 0),
            data_limite=data_limite,
            lead_time_util=lead_time_util,
            status=status,
            homolog_revision=item.reference_revision,
            measurement_revision=item.measurement_revision,
            homolog_date=item.start_date,
            cycle_index=1,
            engineering_status=item.engineering_status,
            qtd_pi=int(item.qtd_pi or 0),
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

        def compute() -> dict[str, List[LMPDashboardItem]]:
            resolved_status = resolve_dashboard_status_filter(status_filter)
            query_request = replace(request, include_qtd_pi=True)

            rows: List[LMP] = self._repository.list_lmps(query_request)
            enriched_all = [self._enrich_item(row) for row in rows]
            lmp_enriched = [
                item for item in enriched_all if item.listing_kind == LISTING_KIND_LMP
            ]
            filtered = self._filter_items_by_status(enriched_all, resolved_status)
            return {
                "all": enriched_all,
                "lmp_only": lmp_enriched,
                "filtered": filtered,
            }

        cached = get_or_set_cached_lmp_dashboard(base_key, compute)
        return cached["all"], cached["lmp_only"], cached["filtered"]

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

    def _summary_rows_cache_key(
        self,
        request: ListLMPRequest,
        *,
        mode: SummaryLoadMode,
    ) -> str:
        suffix = (
            _SUMMARY_ROWS_CACHE_SUFFIX_KPI
            if mode == "kpi"
            else _SUMMARY_ROWS_CACHE_SUFFIX_FULL
        )
        return self._build_base_cache_key(request, "Todos") + suffix

    def _deserialize_dashboard_items(
        self,
        rows: list[dict[str, Any]],
    ) -> List[LMPDashboardItem]:
        allowed = {field.name for field in fields(LMPDashboardItem)}
        return [
            LMPDashboardItem(**{key: row[key] for key in allowed if key in row})
            for row in rows
        ]

    def _enrich_summary_row(self, row: dict[str, Any]) -> LMPDashboardItem:
        nivel, sla_days, sla_minutes, data_limite, lead_time_util, status = (
            LMPBusinessRules.get_dashboard_status(
                start_date_str=row.get("start_date"),
                end_date_str=row.get("end_date"),
                qtd_pi=row.get("qtd_pi"),
                engineering_status=row.get("engineering_status"),
                engineering_total_minutes=row.get("engineering_total_minutes"),
            )
        )
        return LMPDashboardItem(
            branch=row.get("branch"),
            sale_number=row.get("sale_number"),
            sale_description=row.get("sale_description") or "",
            listing_kind=row.get("listing_kind"),
            start_date=row.get("start_date"),
            end_date=row.get("end_date"),
            nivel=nivel,
            dias_uteis_sla=sla_days,
            sla_minutos=sla_minutes,
            engineering_total_minutes=int(row.get("engineering_total_minutes") or 0),
            data_limite=data_limite,
            lead_time_util=lead_time_util,
            status=status,
            homolog_revision=row.get("homolog_revision"),
            measurement_revision=row.get("measurement_revision"),
            homolog_date=row.get("homolog_date") or row.get("start_date"),
            cycle_index=int(row.get("cycle_index") or 1),
            engineering_status=row.get("engineering_status"),
            qtd_pi=int(row.get("qtd_pi") or 0),
        )

    def _ov_key_from_summary_row(self, row: dict[str, Any]) -> dict[str, str] | None:
        branch = str(row.get("branch") or "").strip()
        sale_number = str(row.get("sale_number") or "").strip()
        revision = str(
            row.get("homolog_revision")
            or row.get("measurement_revision")
            or ""
        ).strip()
        if not branch or not sale_number or not revision:
            return None
        return {
            "branch": branch,
            "sale_number": sale_number,
            "revision": revision,
        }

    def _load_raw_summary_rows_kpi(self, request: ListLMPRequest) -> list[dict[str, Any]]:
        """Fatos sem PI + BOM só para OVs FINALIZADA (cards SI / summary)."""
        facts = self._repository.get_lmp_dashboard_summary_facts(request)
        finished_keys: list[dict[str, str]] = []
        for row in facts:
            if not LMPBusinessRules.is_engineering_finished(row.get("engineering_status")):
                continue
            key = self._ov_key_from_summary_row(row)
            if key is not None:
                finished_keys.append(key)

        pi_map: dict[tuple[str, str, str], int] = {}
        if finished_keys:
            pi_map = self._repository.get_lmp_pi_counts_by_ovs(
                ov_keys=finished_keys,
                requested_branch=request.branch,
            )

        merged: list[dict[str, Any]] = []
        for row in facts:
            item = dict(row)
            key = self._ov_key_from_summary_row(row)
            if (
                key is not None
                and LMPBusinessRules.is_engineering_finished(row.get("engineering_status"))
            ):
                item["qtd_pi"] = int(
                    pi_map.get(
                        (key["branch"], key["sale_number"], key["revision"]),
                        0,
                    )
                )
            else:
                item["qtd_pi"] = 0
            merged.append(item)
        return merged

    def _load_raw_summary_rows_full(self, request: ListLMPRequest) -> list[dict[str, Any]]:
        """Batch completo com PI em todas as candidatas (charts / items / nível)."""
        query_request = replace(request, include_qtd_pi=True)
        return self._repository.get_lmp_dashboard_summary(query_request)

    def _load_summary_rows(
        self,
        request: ListLMPRequest,
        *,
        mode: SummaryLoadMode = "full",
    ) -> List[LMPDashboardItem]:
        """Carrega campos de KPI via query summary; singleflight no cold path."""
        cache_key = self._summary_rows_cache_key(request, mode=mode)

        def compute() -> dict[str, list[dict[str, Any]]]:
            raw_rows = (
                self._load_raw_summary_rows_kpi(request)
                if mode == "kpi"
                else self._load_raw_summary_rows_full(request)
            )
            items = [self._enrich_summary_row(row) for row in raw_rows]
            return {"rows": [asdict(item) for item in items]}

        cached = get_or_set_cached_lmp_dashboard(cache_key, compute)
        rows = cached.get("rows") if isinstance(cached, dict) else None
        if isinstance(rows, list):
            return self._deserialize_dashboard_items(rows)
        return []

    def execute_summary(
        self,
        request: ListLMPRequest,
        status_filter: str = "Todos",
        *,
        summary_mode: SummaryLoadMode = "kpi",
    ) -> Dict[str, Any]:
        """Fase 1: KPIs — default `kpi` (PI só FINALIZADA)."""
        cache_key = (
            self._build_base_cache_key(request, status_filter)
            + f"|summary-response|{summary_mode}"
        )

        def compute() -> Dict[str, Any]:
            items = self._load_summary_rows(request, mode=summary_mode)
            lmp_only = [i for i in items if i.listing_kind == LISTING_KIND_LMP]
            resolved_status = resolve_dashboard_status_filter(status_filter)
            filtered = self._filter_items_by_status(items, resolved_status)
            return self._compute_summary(lmp_only, len(filtered))

        return get_or_set_cached_lmp_dashboard(cache_key, compute)

    def execute_charts(
        self,
        request: ListLMPRequest,
        status_filter: str = "Todos",
    ) -> Dict[str, Any]:
        """Fase 2: gráficos — precisa de nível/PI completo (`full`)."""
        cache_key = self._build_base_cache_key(request, status_filter) + "|charts-response"

        def compute() -> Dict[str, Any]:
            items = self._load_summary_rows(request, mode="full")
            resolved_status = resolve_dashboard_status_filter(status_filter)
            filtered = self._filter_items_by_status(items, resolved_status)
            return self._build_charts(filtered)

        cached = get_or_set_cached_lmp_dashboard(cache_key, compute)
        if isinstance(cached, dict) and "levelData" in cached:
            return cached
        return self._build_charts([])

    def execute_items(
        self,
        request: ListLMPRequest,
        status_filter: str = "Todos",
    ) -> Dict[str, Any]:
        """Fase 3: itens paginados — reutiliza summary rows em modo `full`."""
        items = self._load_summary_rows(request, mode="full")
        resolved_status = resolve_dashboard_status_filter(status_filter)
        filtered = self._filter_items_by_status(items, resolved_status)
        total = len(filtered)

        page = request.page or 1
        page_size = request.page_size or DEFAULT_DASHBOARD_PAGE_SIZE
        start = (page - 1) * page_size
        end = start + page_size
        paginated = filtered[start:end]

        return {
            "items": [item.to_dict() for item in paginated],
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
            "items": [item.to_dict() for item in paginated],
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": self._compute_summary(lmp_enriched, total),
            "charts": self._build_charts(filtered),
        }
        set_cached_lmp_dashboard(cache_key, result)
        return result
