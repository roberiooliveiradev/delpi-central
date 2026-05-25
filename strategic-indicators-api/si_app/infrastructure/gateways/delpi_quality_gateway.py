from __future__ import annotations

from si_app.application.dto.nonconformity.list_nonconformity_request import ListNonconformityRequest
from si_app.application.models.page import Page
from si_app.domain.entities.nonconformity.nonconformity import Nonconformity
from si_app.domain.entities.ppm.ppm_item import PpmItem
from si_app.domain.entities.ppm.ppm_summary import PpmSummary
from si_app.domain.ports.nonconformity.nonconformity_query_repository_port import NonconformityQueryRepositoryPort
from si_app.domain.ports.ppm.ppm_query_repository_port import PpmQueryRepositoryPort

from si_app.infrastructure.http.auth_header import bearer_authorization_from_context
from delpi_api_client import DelpiApiClient


def _opt_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class DelpiPpmGateway(PpmQueryRepositoryPort):
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client

    def get_summary(self, request) -> PpmSummary:
        data = self._client.get_ppm_summary(
            request.type,
            params={
                "branch": getattr(request, "branch", None),
                "date_start": getattr(request, "date_start", None),
                "date_end": getattr(request, "date_end", None),
            },
            authorization=bearer_authorization_from_context(),
        )
        return PpmSummary(
            type=request.type,
            branch=data.get("branch") or getattr(request, "branch", None),
            date_start=data.get("date_start") or getattr(request, "date_start", None),
            date_end=data.get("date_end") or getattr(request, "date_end", None),
            total_devolvido_un=float(data.get("total_devolvido_un") or 0),
            total_produzido_milheiro=float(data.get("total_produzido_milheiro") or 0),
            total_produzido_un=float(data.get("total_produzido_un") or 0),
            ppm=float(data.get("ppm") or 0),
        )

    def list_items(self, request) -> Page[PpmItem]:
        data = self._client.list_ppm(
            request.type,
            params={
                "branch": getattr(request, "branch", None),
                "date_start": getattr(request, "date_start", None),
                "date_end": getattr(request, "date_end", None),
                "page": str(request.page) if getattr(request, "page", None) else None,
                "page_size": str(request.page_size) if getattr(request, "page_size", None) else None,
            },
            authorization=bearer_authorization_from_context(),
        )
        items_raw = data.get("items") or []
        items = [
            PpmItem(
                branch=it.get("branch", ""),
                registered_date=it.get("registered_date"),
                code=it.get("code", ""),
                revision=it.get("revision", ""),
                item_code=it.get("item_code"),
                description=it.get("description"),
                returned_quantity_original=it.get("returned_quantity_original"),
                returned_quantity_un=float(it.get("returned_quantity_un") or 0),
            )
            for it in items_raw
        ]
        return Page(
            items=items,
            total=int(data.get("total") or len(items)),
            page=int(data.get("page") or 1),
            page_size=int(data.get("page_size") or len(items)),
        )

    def list_branches(
        self,
        *,
        ppm_type: str,
        date_start: str | None,
        date_end: str | None,
    ) -> list[str]:
        data = self._client.list_quality_branches(
            params={"date_start": date_start, "date_end": date_end},
            authorization=bearer_authorization_from_context(),
        )
        branches = data.get("branches") or data.get("items") or []
        if isinstance(branches, list) and all(isinstance(b, str) for b in branches):
            return branches
        return [str(b) for b in branches if b]


class DelpiNonconformityGateway(NonconformityQueryRepositoryPort):
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client

    def list_nonconformities(self, request: ListNonconformityRequest) -> Page[Nonconformity]:
        data = self._client.list_nonconformities(
            params={
                "type": getattr(request, "type", "all"),
                "branch": getattr(request, "branch", None),
                "date_start": getattr(request, "date_start", None),
                "date_end": getattr(request, "date_end", None),
                "status": getattr(request, "status", None),
                "item_code": getattr(request, "item_code", None),
                "description": getattr(request, "description", None),
                "page": str(request.page) if getattr(request, "page", None) else None,
                "page_size": str(request.page_size) if getattr(request, "page_size", None) else None,
            },
            authorization=bearer_authorization_from_context(),
        )
        items_raw = data.get("items") or []
        items = [
            Nonconformity(
                branch=it.get("branch", ""),
                code=it.get("code", ""),
                revision=it.get("revision", ""),
                type_code=it.get("type_code", ""),
                type_label=it.get("type_label"),
                status_code=it.get("status_code"),
                status_label=it.get("status_label"),
                description=it.get("description"),
                item_code=it.get("item_code"),
                op_code=it.get("op_code"),
                registered_date=it.get("registered_date"),
                occurrence_date=it.get("occurrence_date"),
                priority_code=it.get("priority_code"),
                priority_label=it.get("priority_label"),
                origin_department=it.get("origin_department"),
                destination_department=it.get("destination_department"),
                customer_code=it.get("customer_code"),
                customer_store=it.get("customer_store"),
                supplier_code=it.get("supplier_code"),
                supplier_store=it.get("supplier_store"),
                produced_quantity=_opt_float(it.get("produced_quantity")),
                returned_quantity=_opt_float(it.get("returned_quantity")),
            )
            for it in items_raw
        ]
        return Page(
            items=items,
            total=int(data.get("total") or len(items)),
            page=int(data.get("page") or 1),
            page_size=int(data.get("page_size") or len(items)),
        )