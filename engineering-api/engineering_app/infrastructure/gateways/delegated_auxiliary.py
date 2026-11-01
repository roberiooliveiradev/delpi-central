"""Adapters auxiliares delegados — owners oficiais via Bearer humano (G5).

Mesmo padrão de `overview_api_delpi.py`: a Engineering API NÃO reimplementa
regras de metas/IDD (Strategic Indicators), não conformidades (NC —
api-delpi plugin Postgres) nem catálogo de produtos/estrutura (Products).
Ela delega o Bearer humano às rotas oficiais dos owners; a autorização
efetiva downstream decide — 401/403 viram `forbidden` honesto, nunca
payload inventado nem bypass privilegiado.

Rotas oficiais consumidas:
- `GET /engineering/lmps/dashboard/summary` — campos de meta enriquecidos
  pelo SI (`DashboardGoalFields`); owner LMP/SI.
- `GET /dashboard/department-idd` — nota IDD departamental; owner SI.
- `GET /engineering/lmps/nonconformities/streak` — dias sem NC; owner NC.
- `GET /products/{code}/structure` — BOM/estrutura; owner Products.
"""

from __future__ import annotations

import logging
from typing import Any

from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.infrastructure.gateways.downstream_client import (
    DownstreamClient,
    DownstreamError,
)

logger = logging.getLogger(__name__)

_GOAL_FIELD_KEYS = (
    "has_goal",
    "goal_label",
    "goal_value",
    "comparable_goal",
    "reference_goal",
    "target",
    "goal_aggregation",
    "goal_mode",
    "goal_period_kind",
    "goal_period_partial",
    "goal_scope_branch",
    "goal_scope_label",
    "goal_scope_hint",
    "scope_type",
    "performance_direction",
    "value_unit",
    "value_prefix",
    "value_suffix",
    "value_decimals",
)


def _lmp_date(value: str | None) -> str | None:
    """YYYY-MM-DD → YYYYMMDD (contrato legado LMP); outros passam."""
    if not value:
        return None
    stripped = value.strip()
    if len(stripped) == 10 and stripped[4] == "-" and stripped[7] == "-":
        return stripped.replace("-", "")
    return stripped


def _map_error(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, DownstreamError) and exc.status_code in (401, 403):
        return {"status": "forbidden", "reason": "owner_denied"}
    if isinstance(exc, DownstreamError) and exc.status_code == 404:
        return {"status": "not_found", "reason": "not_found"}
    if isinstance(exc, DownstreamError):
        return {
            "status": "unavailable",
            "reason": exc.kind if exc.kind != "http" else "upstream_error",
        }
    logger.warning("delegated_auxiliary_unexpected_error", exc_info=True)
    return {"status": "unavailable", "reason": "upstream_error"}


class ApiDelpiDelegatedAuxiliary:
    """READs governados delegados aos owners oficiais (sem S2S: a
    autorização é a permissão efetiva do próprio humano downstream)."""

    def __init__(self, client: DownstreamClient) -> None:
        self._client = client

    async def fetch_goal_context(
        self,
        ctx: HomeSourceContext,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> dict[str, Any]:
        """Campos de meta (SI) do summary oficial — somente goal_*."""
        try:
            data = await self._client.get(
                "/engineering/lmps/dashboard/summary",
                params={
                    "start_date": _lmp_date(start_date),
                    "end_date": _lmp_date(end_date),
                    "branch": branch,
                },
                access_token=ctx.access_token,
                request_id=ctx.request_id,
            )
        except Exception as exc:
            return _map_error(exc)

        if not isinstance(data, dict):
            return {"status": "unavailable", "reason": "contract_error"}

        goal_fields = {
            key: data[key] for key in _GOAL_FIELD_KEYS if key in data
        }
        return {
            "status": "available" if goal_fields else "empty",
            "data": goal_fields,
        }

    async def _get_json(
        self,
        ctx: HomeSourceContext,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """GET JSON delegado → ``{"status", "data"}`` honesto."""
        try:
            data = await self._client.get(
                path,
                params=params,
                access_token=ctx.access_token,
                request_id=ctx.request_id,
            )
        except Exception as exc:
            return _map_error(exc)

        if not isinstance(data, dict):
            return {"status": "unavailable", "reason": "contract_error"}
        return {"status": "available", "data": data}

    async def fetch_department_idd(
        self,
        ctx: HomeSourceContext,
        *,
        competence: str | None,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> dict[str, Any]:
        return await self._get_json(
            ctx,
            "/dashboard/department-idd",
            {
                "department_id": "engineering",
                "competence": competence,
                "start_date": start_date,
                "end_date": end_date,
                "branch": branch,
            },
        )

    async def fetch_nc_streak(
        self,
        ctx: HomeSourceContext,
    ) -> dict[str, Any]:
        return await self._get_json(
            ctx, "/engineering/lmps/nonconformities/streak"
        )

    # --- Products (E-PRD) ---------------------------------------------------

    async def fetch_product_search(
        self,
        ctx: HomeSourceContext,
        *,
        code: str | None = None,
        description: str | None = None,
        group_code: str | None = None,
        subgroup: str | None = None,
        product_type: str | None = None,
        customer_reference: str | None = None,
        page: int = 1,
        page_size: int = 50,
        sort: str | None = None,
        direction: str | None = None,
    ) -> dict[str, Any]:
        return await self._get_json(
            ctx,
            "/products/search",
            {
                "code": code,
                "description": description,
                "group_code": group_code,
                "subgroup": subgroup,
                "product_type": product_type,
                "customer_reference": customer_reference,
                "view": "engineering",
                "page": page,
                "page_size": page_size,
                "sort": sort,
                "direction": direction,
            },
        )

    async def fetch_product_filter_options(
        self, ctx: HomeSourceContext
    ) -> dict[str, Any]:
        return await self._get_json(ctx, "/products/filter-options")

    async def fetch_product_detail(
        self,
        ctx: HomeSourceContext,
        *,
        code: str,
        view: str = "engineering",
    ) -> dict[str, Any]:
        return await self._get_json(
            ctx, f"/products/{code}", {"view": view}
        )

    async def fetch_product_structure(
        self,
        ctx: HomeSourceContext,
        *,
        code: str,
        max_depth: int = 6,
        page_size: int = 200,
    ) -> dict[str, Any]:
        return await self._get_json(
            ctx,
            f"/products/{code}/structure",
            {"max_depth": max_depth, "page_size": page_size},
        )

    async def fetch_product_parents(
        self,
        ctx: HomeSourceContext,
        *,
        code: str,
        max_depth: int | None = None,
        page: int = 1,
        page_size: int = 200,
    ) -> dict[str, Any]:
        return await self._get_json(
            ctx,
            f"/products/{code}/parents",
            {
                "max_depth": max_depth,
                "page": page,
                "page_size": page_size,
            },
        )

    async def fetch_product_suppliers(
        self,
        ctx: HomeSourceContext,
        *,
        code: str,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        return await self._get_json(
            ctx,
            f"/products/{code}/suppliers",
            {"page": page, "page_size": page_size, "view": "engineering"},
        )

    async def fetch_product_drawing(
        self,
        ctx: HomeSourceContext,
        *,
        code: str,
    ) -> dict[str, Any]:
        """Metadados do desenho PDF do acervo oficial (Cockpit/file server)."""
        return await self._get_json(ctx, f"/products/{code}/drawing")

    async def fetch_product_drawing_pdf(
        self,
        ctx: HomeSourceContext,
        *,
        code: str,
    ) -> dict[str, Any]:
        """Bytes do PDF do desenho — proxy governado, nunca file share."""
        try:
            status, headers, content = await self._client.get_raw(
                f"/products/{code}/drawing/pdf",
                access_token=ctx.access_token,
                request_id=ctx.request_id,
            )
        except Exception as exc:
            return _map_error(exc)
        return {
            "status": "available",
            "status_code": status,
            "content": content,
            "content_type": headers.get("content-type", "application/pdf"),
            "content_disposition": headers.get("content-disposition", ""),
        }

    async def fetch_product_purchase_price_history(
        self,
        ctx: HomeSourceContext,
        *,
        code: str,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
        history_limit: int | None = None,
    ) -> dict[str, Any]:
        return await self._get_json(
            ctx,
            f"/products/{code}/purchase-price-history",
            {
                "start_date": start_date,
                "end_date": end_date,
                "branch": branch,
                "history_limit": history_limit,
            },
        )
