from __future__ import annotations

from typing import Any

from financial_app.application.services.content_loader import load_content
from financial_app.application.services.payload_mapping import (
    as_float,
    as_int,
    as_opt_str,
    as_str,
    clamp_limit,
    clamp_page,
    clamp_page_size,
    map_pagination,
    map_period,
    map_sort,
    unwrap_data,
)
from financial_app.domain.services.period_range import (
    resolve_inclusive_period_or_default,
    rolling_month_series_bounds,
)
from financial_app.application.services.response_cache import cached_fetch
from financial_app.core.security import FIN_COST_CENTERS_VIEW
from financial_app.domain.errors import FinancialError
from financial_app.domain.ports.financial_data_gateway import FinancialDataGateway
from financial_app.domain.services.branch_access_service import BranchAccessService


class InvalidCostCenterQuery(FinancialError):
    """Filtro, ordenação ou paginação fora do catálogo de centros de custo."""


def _settings() -> dict[str, Any]:
    return load_content("cost_centers.json")


class CostCenterService:
    def __init__(
        self,
        gateway: FinancialDataGateway,
        *,
        branch_access: BranchAccessService | None = None,
    ) -> None:
        self._gateway = gateway
        self._branch_access = branch_access or BranchAccessService()

    def filters(
        self,
        user: object | None,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
        cost_center: str | None = None,
        exclude_mp_products: bool = False,
        refresh: bool = False,
    ) -> dict[str, Any]:
        scope, start, end = self._prepare(user, branch, start_date, end_date)
        payload = self._cached(
            "filters",
            {"branch": scope, "start": start, "end": end, "cc": cost_center, "xmp": exclude_mp_products},
            lambda: unwrap_data(
                self._gateway.fetch_cost_center_filters(
                    start_date=start,
                    end_date=end,
                    branch=scope,
                    cost_center=cost_center,
                    exclude_mp_products=exclude_mp_products,
                )
            ),
            refresh=refresh,
        )
        return {
            "period": map_period(payload.get("periodo")),
            "branch": scope,
            "branches": [
                {"code": as_str(item.get("filial")), "label": as_str(item.get("descricao"))}
                for item in payload.get("filiais") or []
                if isinstance(item, dict)
            ],
            "costCenters": [
                {"code": as_str(item.get("codigo")), "label": as_str(item.get("descricao"))}
                for item in payload.get("centros_custo") or []
                if isinstance(item, dict)
            ],
            "suppliers": [
                {
                    "code": as_str(item.get("codigo")),
                    "store": as_str(item.get("loja")),
                    "label": as_str(item.get("razao_social")),
                }
                for item in payload.get("fornecedores") or []
                if isinstance(item, dict)
            ],
        }

    def summary(
        self,
        user: object | None,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
        cost_center: str | None,
        supplier_code: str | None,
        supplier_store: str | None,
        exclude_mp_products: bool = False,
        refresh: bool = False,
    ) -> dict[str, Any]:
        scope, start, end = self._prepare(user, branch, start_date, end_date)
        payload = self._cached(
            "summary",
            {
                "branch": scope,
                "start": start,
                "end": end,
                "cc": cost_center,
                "supplier": supplier_code,
                "store": supplier_store,
                "xmp": exclude_mp_products,
            },
            lambda: unwrap_data(
                self._gateway.fetch_cost_center_summary(
                    start_date=start,
                    end_date=end,
                    branch=scope,
                    cost_center=cost_center,
                    supplier_code=supplier_code,
                    supplier_store=supplier_store,
                    exclude_mp_products=exclude_mp_products,
                )
            ),
            refresh=refresh,
        )
        return {
            "period": map_period(payload.get("periodo")),
            "branch": scope,
            "totalAmount": as_float(payload.get("total_periodo")),
            "entryCount": as_int(payload.get("quantidade_lancamentos")),
            "costCenterCount": as_int(payload.get("quantidade_centros_custo")),
            "supplierCount": as_int(payload.get("quantidade_fornecedores")),
            "averageTicket": as_float(payload.get("ticket_medio")),
            "largestEntry": as_float(payload.get("maior_lancamento")),
        }

    def series(
        self,
        user: object | None,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
        cost_center: str | None,
        supplier_code: str | None,
        supplier_store: str | None,
        exclude_mp_products: bool = False,
        refresh: bool = False,
    ) -> dict[str, Any]:
        scope, _, _ = self._prepare(user, branch, start_date, end_date)
        series_cfg = _settings().get("series") or {}
        series_months = as_int(series_cfg.get("months"), 12)
        start, end = rolling_month_series_bounds(
            start_date,
            end_date,
            months=series_months,
        )
        payload = self._cached(
            "series",
            {
                "branch": scope,
                "start": start,
                "end": end,
                "cc": cost_center,
                "supplier": supplier_code,
                "store": supplier_store,
                "xmp": exclude_mp_products,
            },
            lambda: unwrap_data(
                self._gateway.fetch_cost_center_series(
                    start_date=start,
                    end_date=end,
                    branch=scope,
                    cost_center=cost_center,
                    supplier_code=supplier_code,
                    supplier_store=supplier_store,
                    exclude_mp_products=exclude_mp_products,
                )
            ),
            refresh=refresh,
        )
        return {
            "period": map_period(payload.get("periodo")),
            "branch": scope,
            "items": [
                {
                    "yearMonth": as_str(item.get("ano_mes")),
                    "year": as_int(item.get("ano")),
                    "month": as_int(item.get("mes")),
                    "totalAmount": as_float(item.get("valor_total")),
                    "entryCount": as_int(item.get("quantidade_lancamentos")),
                }
                for item in payload.get("serie") or []
                if isinstance(item, dict)
            ],
        }

    def ranking_cost_centers(
        self,
        user: object | None,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
        supplier_code: str | None,
        supplier_store: str | None,
        limit: int | None,
        exclude_mp_products: bool = False,
        refresh: bool = False,
    ) -> dict[str, Any]:
        scope, start, end = self._prepare(user, branch, start_date, end_date)
        ranking_cfg = _settings().get("ranking") or {}
        capped = clamp_limit(
            limit,
            default=as_int(ranking_cfg.get("defaultLimit"), 10),
            maximum=as_int(ranking_cfg.get("maxLimit"), 50),
        )
        payload = self._cached(
            "rankingCostCenters",
            {
                "branch": scope,
                "start": start,
                "end": end,
                "supplier": supplier_code,
                "store": supplier_store,
                "limit": capped,
                "xmp": exclude_mp_products,
            },
            lambda: unwrap_data(
                self._gateway.fetch_cost_center_ranking_centers(
                    start_date=start,
                    end_date=end,
                    branch=scope,
                    supplier_code=supplier_code,
                    supplier_store=supplier_store,
                    limit=capped,
                    exclude_mp_products=exclude_mp_products,
                )
            ),
            refresh=refresh,
        )
        return {
            "period": map_period(payload.get("periodo")),
            "branch": scope,
            "limit": capped,
            "items": [
                {
                    "code": as_str(item.get("centro_custo_codigo")),
                    "label": as_str(item.get("centro_custo_descricao")),
                    "totalAmount": as_float(item.get("valor_total")),
                    "entryCount": as_int(item.get("quantidade_lancamentos")),
                    "percentage": as_float(item.get("percentual")),
                }
                for item in payload.get("ranking") or []
                if isinstance(item, dict)
            ],
        }

    def ranking_suppliers(
        self,
        user: object | None,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
        cost_center: str | None,
        limit: int | None,
        exclude_mp_products: bool = False,
        refresh: bool = False,
    ) -> dict[str, Any]:
        scope, start, end = self._prepare(user, branch, start_date, end_date)
        ranking_cfg = _settings().get("ranking") or {}
        capped = clamp_limit(
            limit,
            default=as_int(ranking_cfg.get("defaultLimit"), 10),
            maximum=as_int(ranking_cfg.get("maxLimit"), 50),
        )
        payload = self._cached(
            "rankingSuppliers",
            {
                "branch": scope,
                "start": start,
                "end": end,
                "cc": cost_center,
                "limit": capped,
                "xmp": exclude_mp_products,
            },
            lambda: unwrap_data(
                self._gateway.fetch_cost_center_ranking_suppliers(
                    start_date=start,
                    end_date=end,
                    branch=scope,
                    cost_center=cost_center,
                    limit=capped,
                    exclude_mp_products=exclude_mp_products,
                )
            ),
            refresh=refresh,
        )
        return {
            "period": map_period(payload.get("periodo")),
            "branch": scope,
            "limit": capped,
            "items": [
                {
                    "code": as_str(item.get("fornecedor_cliente_codigo")),
                    "store": as_str(item.get("loja")),
                    "label": as_str(item.get("razao_social")),
                    "totalAmount": as_float(item.get("valor_total")),
                    "entryCount": as_int(item.get("quantidade_lancamentos")),
                    "percentage": as_float(item.get("percentual")),
                }
                for item in payload.get("ranking") or []
                if isinstance(item, dict)
            ],
        }

    def entries(
        self,
        user: object | None,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
        cost_center: str | None,
        supplier_code: str | None,
        supplier_store: str | None,
        search: str | None,
        page: int,
        page_size: int,
        sort_by: str | None,
        sort_dir: str | None,
        exclude_mp_products: bool = False,
        refresh: bool = False,
    ) -> dict[str, Any]:
        scope, start, end = self._prepare(user, branch, start_date, end_date)
        cfg = _settings()
        pagination = cfg.get("pagination") or {}
        sort_cfg = (cfg.get("sort") or {}).get("entries") or {}
        allowed = {str(item) for item in sort_cfg.get("allowed") or []}
        default_by = str(sort_cfg.get("default") or "data_emissao")
        field = (sort_by or default_by).strip() or default_by
        if field not in allowed:
            template = str((cfg.get("messages") or {}).get("invalidSortBy") or "Ordenação inválida.")
            raise InvalidCostCenterQuery(template.format(allowed=", ".join(sorted(allowed))))
        directions = {str(item) for item in (cfg.get("sort") or {}).get("allowedDirections") or []}
        direction = (sort_dir or "desc").strip().lower() or "desc"
        if direction not in directions:
            raise InvalidCostCenterQuery(
                str((cfg.get("messages") or {}).get("invalidSortDir") or "Direção inválida.")
            )
        page_n = clamp_page(page, 1)
        size_n = clamp_page_size(
            page_size,
            default=as_int(pagination.get("defaultPageSize"), 50),
            maximum=as_int(pagination.get("maxPageSize"), 200),
        )
        payload = self._cached(
            "entries",
            {
                "branch": scope,
                "start": start,
                "end": end,
                "cc": cost_center,
                "supplier": supplier_code,
                "store": supplier_store,
                "search": search,
                "page": page_n,
                "size": size_n,
                "sort": field,
                "dir": direction,
                "xmp": exclude_mp_products,
            },
            lambda: unwrap_data(
                self._gateway.fetch_cost_center_entries(
                    start_date=start,
                    end_date=end,
                    branch=scope,
                    cost_center=cost_center,
                    supplier_code=supplier_code,
                    supplier_store=supplier_store,
                    search=search,
                    page=page_n,
                    page_size=size_n,
                    sort_by=field,
                    sort_dir=direction,
                    exclude_mp_products=exclude_mp_products,
                )
            ),
            refresh=refresh,
        )
        return {
            "period": map_period(payload.get("periodo")),
            "branch": scope,
            "pagination": map_pagination(
                payload.get("pagination"),
                default_page_size=as_int(pagination.get("defaultPageSize"), 50),
            ),
            "sort": map_sort(payload.get("sort"), default_by=field, default_dir=direction),
            "filters": {
                "costCenter": as_opt_str(cost_center),
                "supplierCode": as_opt_str(supplier_code),
                "supplierStore": as_opt_str(supplier_store),
                "search": as_opt_str(search),
                "excludeMpProducts": exclude_mp_products,
            },
            "items": [
                self._map_entry(item)
                for item in payload.get("items") or []
                if isinstance(item, dict)
            ],
        }

    def _prepare(
        self,
        user: object | None,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> tuple[str | None, str, str]:
        self._branch_access.assert_can_use(user, FIN_COST_CENTERS_VIEW)
        scope = self._branch_access.resolve_branch_scope(user, branch)
        start, end = resolve_inclusive_period_or_default(start_date, end_date)
        return scope, start, end

    def _cached(
        self,
        kind: str,
        parts: dict[str, Any],
        loader,
        *,
        refresh: bool,
    ) -> dict[str, Any]:
        ttl = as_int((_settings().get("cacheTtlSeconds") or {}).get(kind), 0)
        key = f"cost-centers:{kind}:{sorted(parts.items())}"
        return cached_fetch(key, ttl, loader, refresh=refresh)

    @staticmethod
    def _map_entry(item: dict[str, Any]) -> dict[str, Any]:
        recno = item.get("recno_sd1")
        return {
            "id": as_str(recno if recno is not None else item.get("id")),
            "branch": as_str(item.get("filial")),
            "issueDate": as_opt_str(item.get("data_emissao")),
            "issueDateLabel": as_str(item.get("data_emissao_formatada")),
            "costCenterCode": as_str(item.get("centro_custo_codigo")),
            "costCenterLabel": as_str(item.get("centro_custo_descricao")),
            "supplierCode": as_str(item.get("fornecedor_cliente_codigo")),
            "supplierStore": as_str(item.get("loja")),
            "supplierName": as_str(item.get("razao_social")),
            "document": as_str(item.get("documento")),
            "series": as_str(item.get("serie")),
            "purchaseOrder": as_str(item.get("pedido")),
            "item": as_str(item.get("item")),
            "orderItem": as_str(item.get("item_pedido")),
            "productCode": as_str(item.get("produto_codigo")),
            "productLabel": as_str(item.get("produto_descricao")),
            "notes": as_str(item.get("observacoes")),
            "quantity": as_float(item.get("quantidade")),
            "unitAmount": as_float(item.get("valor_unitario")),
            "totalAmount": as_float(item.get("valor_total")),
            "ledgerAccount": as_str(item.get("conta_contabil")),
            "apportionment": as_str(item.get("rateio")),
            "tes": as_str(item.get("tes")),
            "cfop": as_str(item.get("cfop")),
            "documentType": as_str(item.get("tipo_documento")),
            "entryType": as_str(item.get("tipo_produto_lancamento")),
        }
