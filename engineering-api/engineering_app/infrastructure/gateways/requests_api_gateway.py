"""Adapters oficiais de leitura — requests-api (owner: Minhas Solicitações).

Contratos comprovados no G0:
- `GET /requests/work-queue` — fila de trabalho/pendências atribuídas ao
  usuário autenticado (escopo server-side por usuário).
- `GET /requests/mine` — solicitações criadas pelo usuário autenticado.

Envelope: `{"success", "data": {"items": [...], "total", "page", "page_size"}}`.
Item (serialize_request): id, request_number, type_code, status,
status_alias, priority, branch_code, created_at, updated_at.
Delegação: Bearer do usuário + headers internos oficiais — a requests-api
revalida o acesso do módulo `my-requests` e o escopo por usuário.
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

_SYSTEM = "requests-api"
# Superfície existente do Portal para abrir uma solicitação (manifest
# oficial do MFE my-requests — basePath comprovado no G0).
_REQUESTS_HREF = "/apps/my-requests"


def _map_request_item(raw: Any, *, kind: str) -> HomeItem:
    if not isinstance(raw, dict) or not raw.get("id"):
        raise DownstreamError("contract_error", "Item de request sem id.")
    request_number = str(raw.get("request_number") or raw["id"])
    meta = {
        "request_number": request_number,
        "type_code": raw.get("type_code"),
        "priority": raw.get("priority"),
        "branch_code": raw.get("branch_code"),
        "allowed_actions": list(raw.get("allowed_actions") or []),
    }
    return HomeItem(
        id=str(raw["id"]),
        kind=kind,
        title=request_number,
        status=raw.get("status"),
        status_label=raw.get("status_alias") or raw.get("status"),
        date=raw.get("updated_at") or raw.get("created_at"),
        href=_REQUESTS_HREF,
        source=_SYSTEM,
        meta=meta,
    )


class _RequestsApiSource:
    endpoint = ""
    _kind = "request"

    def __init__(self, client: DownstreamClient) -> None:
        self._client = client

    async def fetch(self, ctx: HomeSourceContext, *, limit: int) -> SectionFetch:
        path = self.endpoint.split(" ", 1)[1]
        try:
            data = await self._client.get(
                path,
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
        except Exception:  # pragma: no cover - defesa residual
            logger.warning("requests_api_unexpected_error", exc_info=True)
            return SectionFetch(status="unavailable", reason="upstream_error")

        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            return SectionFetch(status="unavailable", reason="contract_error")

        try:
            items = tuple(
                _map_request_item(raw, kind=self._kind) for raw in data["items"]
            )
        except DownstreamError:
            return SectionFetch(status="unavailable", reason="contract_error")

        total = data.get("total") if isinstance(data.get("total"), int) else None
        if not items:
            return SectionFetch(status="empty", total=total or 0)
        return SectionFetch(status="available", items=items, total=total)


class RequestsApiWorkQueueSource(_RequestsApiSource):
    system = _SYSTEM
    endpoint = "GET /requests/work-queue"
    _kind = "task"


class RequestsApiMineSource(_RequestsApiSource):
    system = _SYSTEM
    endpoint = "GET /requests/mine"
    _kind = "request"
