"""Adapter oficial de leitura — api-delpi Engineering (owner: api-delpi/TOTVS).

Contrato comprovado no G0:
- `GET /engineering/lmps` — lista paginada de LMPs. AuthZ downstream:
  `ENGINEERING_LMP_ACCESS` via `require_any_permission` (403 → seção
  `forbidden`, sem exposição de existência/dados).

Envelope: `api_delpi_success` → `{"success", "data": {"items": [LMP], "total",
"total_pages", ...}, "meta": {"operationId": "list_lmps", ...}}`.
Item LMP (domain entity): sale_number, sale_description, engineering_status,
branch, start_date, end_date, reference_revision, measurement_revision,
costumer_name, seller_name.

A api-delpi permanece autoridade das regras de LMP — este adapter apenas
normaliza o resumo oficial; nenhuma regra de criticidade/status é derivada.
"""

from __future__ import annotations

import logging
from typing import Any

from engineering_app.application.models.home import HomeItem
from engineering_app.application.ports.home_sources import (
    HomeSourceContext,
    SectionFetch,
)
from engineering_app.infrastructure.gateways.downstream_client import (
    DownstreamClient,
    DownstreamError,
)

logger = logging.getLogger(__name__)

_SYSTEM = "api-delpi"
# Superfície existente do Portal para LMPs (manifest oficial do MFE
# dashboard-lmps — basePath comprovado no G0).
_LMPS_HREF = "/apps/dashboard-lmps"


def _map_lmp_item(raw: Any) -> HomeItem:
    if not isinstance(raw, dict) or not raw.get("sale_number"):
        raise DownstreamError("contract_error", "Item de LMP sem sale_number.")
    sale_number = str(raw["sale_number"])
    meta = {
        "sale_number": sale_number,
        "branch": raw.get("branch"),
        "costumer_name": raw.get("costumer_name"),
        "reference_revision": raw.get("reference_revision"),
        "measurement_revision": raw.get("measurement_revision"),
        "start_date": raw.get("start_date"),
        "end_date": raw.get("end_date"),
    }
    return HomeItem(
        id=sale_number,
        kind="lmp",
        title=raw.get("sale_description") or sale_number,
        status=raw.get("engineering_status"),
        status_label=raw.get("engineering_status"),
        date=raw.get("end_date") or raw.get("start_date"),
        href=_LMPS_HREF,
        source=_SYSTEM,
        meta=meta,
    )


class ApiDelpiLmpSource:
    system = _SYSTEM
    endpoint = "GET /engineering/lmps"

    def __init__(self, client: DownstreamClient) -> None:
        self._client = client

    async def fetch(self, ctx: HomeSourceContext, *, limit: int) -> SectionFetch:
        try:
            data = await self._client.get(
                "/engineering/lmps",
                params={"page": 1, "page_size": limit},
                access_token=ctx.access_token,
                request_id=ctx.request_id,
            )
        except DownstreamError as exc:
            if exc.status_code in (401, 403):
                return SectionFetch(
                    status="forbidden",
                    message="Acesso negado pelo owner da fonte.",
                )
            return SectionFetch(
                status="unavailable",
                reason=exc.kind if exc.kind != "http" else "upstream_error",
            )
        except Exception:
            logger.warning("api_delpi_lmp_unexpected_error", exc_info=True)
            return SectionFetch(status="unavailable", reason="upstream_error")

        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            return SectionFetch(status="unavailable", reason="contract_error")

        try:
            items = tuple(_map_lmp_item(raw) for raw in data["items"])
        except DownstreamError:
            return SectionFetch(status="unavailable", reason="contract_error")

        total = data.get("total") if isinstance(data.get("total"), int) else None
        if not items:
            return SectionFetch(status="empty", total=total or 0)
        return SectionFetch(status="available", items=items, total=total)
