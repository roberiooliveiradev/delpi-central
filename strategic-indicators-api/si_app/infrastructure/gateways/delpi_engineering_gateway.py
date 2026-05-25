from __future__ import annotations

from typing import List

from si_app.application.dto.lmp.get_lmp_request import GetLMPRequest
from si_app.application.dto.lmp.list_lmp_request import ListLMPRequest
from si_app.application.models.page import Page
from si_app.domain.entities.lmp.lmp import LMP
from si_app.domain.entities.lmp.lmp_product import LMPProduct
from si_app.domain.ports.lmp.lmp_query_repository_port import LMPQueryRepositoryPort

from si_app.infrastructure.http.auth_header import bearer_authorization_from_context
from delpi_api_client import DelpiApiClient

_LARGE_PAGE = 5000


def _opt_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _build_lmp_params(request: ListLMPRequest, **extra: str | None) -> dict[str, str | None]:
    params: dict[str, str | None] = {
        "date_start": request.date_start,
        "date_end": request.date_end,
        "branch": request.branch,
        "listing_type": request.listing_type,
    }
    if getattr(request, "include_qtd_pi", None) is not None:
        params["include_qtd_pi"] = str(request.include_qtd_pi).lower()
    params.update(extra)
    return params


def _parse_lmp(raw: dict) -> LMP:
    products_raw = raw.get("list_products") or []
    products = [
        LMPProduct(**{k: p.get(k) for k in LMPProduct.__dataclass_fields__})
        if isinstance(p, dict) else p
        for p in products_raw
    ]
    return LMP(
        branch=raw.get("branch"),
        sale_number=raw.get("sale_number", ""),
        sale_description=raw.get("sale_description", ""),
        listing_kind=raw.get("listing_kind"),
        start_date=raw.get("start_date"),
        end_date=raw.get("end_date"),
        engineering_status=raw.get("engineering_status"),
        qtd_engineering_entries=_opt_int(raw.get("qtd_engineering_entries")),
        qtd_engineering_closed=_opt_int(raw.get("qtd_engineering_closed")),
        qtd_advanced_from_engineering=_opt_int(raw.get("qtd_advanced_from_engineering")),
        qtd_returned_from_engineering=_opt_int(raw.get("qtd_returned_from_engineering")),
        engineering_total_minutes=_opt_int(raw.get("engineering_total_minutes")),
        qtd_pi=_opt_int(raw.get("qtd_pi")),
        costumer_code=raw.get("costumer_code"),
        costumer_store=raw.get("costumer_store"),
        costumer_name=raw.get("costumer_name"),
        seller_code=raw.get("seller_code"),
        seller_name=raw.get("seller_name"),
        list_products=products,
    )


class DelpiLmpGateway(LMPQueryRepositoryPort):
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client

    def list_lmps(self, request: ListLMPRequest) -> List[LMP]:
        params = _build_lmp_params(request, page="1", page_size=str(_LARGE_PAGE))
        data = self._client.list_lmps(
            params=params,
            authorization=bearer_authorization_from_context(),
        )
        items_raw = data.get("items") or []
        return [_parse_lmp(it) for it in items_raw]

    def list_lmps_page(self, request: ListLMPRequest) -> Page[LMP]:
        page = getattr(request, "page", None) or 1
        page_size = getattr(request, "page_size", None) or 50
        params = _build_lmp_params(request, page=str(page), page_size=str(page_size))

        data = self._client.list_lmps(
            params=params,
            authorization=bearer_authorization_from_context(),
        )
        items_raw = data.get("items") or []
        items = [_parse_lmp(it) for it in items_raw]

        return Page(
            items=items,
            total=int(data.get("total") or len(items)),
            page=int(data.get("page") or page),
            page_size=int(data.get("page_size") or page_size),
        )

    def get_lmp(self, request: GetLMPRequest) -> LMP:
        data = self._client.get_lmp(
            request.sale_number,
            authorization=bearer_authorization_from_context(),
        )
        if isinstance(data, list):
            data = data[0] if data else {}
        return _parse_lmp(data)

    def get_lmp_dashboard_summary(self, request: ListLMPRequest) -> list[dict]:
        """Fetch all LMPs and return only the fields needed for dashboard summary."""
        params = _build_lmp_params(request, page="1", page_size=str(_LARGE_PAGE))
        data = self._client.list_lmps(
            params=params,
            authorization=bearer_authorization_from_context(),
        )
        items_raw = data.get("items") or []
        return [
            {
                "branch": it.get("branch"),
                "sale_number": it.get("sale_number"),
                "start_date": it.get("start_date"),
                "end_date": it.get("end_date"),
                "engineering_status": it.get("engineering_status"),
                "engineering_total_minutes": int(it.get("engineering_total_minutes") or 0),
                "qtd_pi": int(it.get("qtd_pi") or 0),
            }
            for it in items_raw
        ]

    def get_computed_dashboard_summary(
        self, request: ListLMPRequest,
    ) -> dict[str, float | int | None]:
        """Call api-delpi's pre-computed summary endpoint (faster than fetching all rows)."""
        params: dict[str, str | None] = {
            "date_start": request.date_start,
            "date_end": request.date_end,
            "branch": request.branch,
        }
        data = self._client.get_lmp_dashboard_summary(
            params=params,
            authorization=bearer_authorization_from_context(),
        )
        return {
            "total_lmps": int(data.get("total_lmps") or 0),
            "percent_dentro_prazo": float(data.get("percent_dentro_prazo") or 0.0),
            "avg_lead_time": float(data.get("avg_lead_time") or 0.0),
        }