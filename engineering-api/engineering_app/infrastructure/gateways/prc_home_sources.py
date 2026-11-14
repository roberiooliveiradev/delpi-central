"""Fontes PRC in-process da Home (ENG-HOME-PRC-NATIVE-INTEGRATION-01).

Opção A ratificada (ledger §31): as seções ``tasks`` e ``requests`` da
Home passam a ser alimentadas pelos casos PRC nativos do próprio domínio
``product_registration`` — mesmo requestId, mesma AuthZ de objeto, sem
HTTP self-call, sem espelho de registros.

- ``tasks``   → fila PRC do analista (``global_scope`` via ``is_analyst``).
- ``requests`` → casos PRC do próprio usuário (``own_scope``).

Os registros corporativos da requests-api deixam de alimentar a Home,
mas permanecem intactos e acessíveis pelo My Requests (owner preservado).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from engineering_app.application.models.home import HomeItem
from engineering_app.application.ports.home_sources import (
    HomeSourceContext,
    SectionFetch,
)
from engineering_app.domain.product_registration.errors import (
    PrcForbiddenError,
)
from engineering_app.domain.product_registration.models import PrcActor

logger = logging.getLogger(__name__)

_SYSTEM = "engineering-api"
_ENDPOINT = "GET /v1/product-registration/requests"
# Rota oficial do detalhe PRC no Portal Engenharia (resolvePrcPath).
_DETAIL_HREF = "/apps/engineering/product-registration"

_TYPE_LABELS = {
    "create": "Cadastro de produto",
    "update": "Alteração de produto",
}


def _map_prc_item(raw: Any, *, kind: str) -> HomeItem:
    if not isinstance(raw, dict) or not raw.get("id"):
        raise ValueError("Item PRC sem id.")
    request_id = str(raw["id"])
    request_type = str(raw.get("requestType") or "")
    official = raw.get("officialCode")
    description = raw.get("description")
    if official:
        title = f"{_TYPE_LABELS.get(request_type, 'Solicitação PRC')} · {official}"
    elif description:
        title = str(description)[:140]
    else:
        title = _TYPE_LABELS.get(request_type, "Solicitação PRC")
    meta = {
        "request_id": request_id,
        "request_type": request_type,
        "official_code": official,
        "case_version": raw.get("caseVersion"),
        "prc_source": raw.get("source"),
        "requester": raw.get("requester"),
        "assigned_to": raw.get("assignedTo"),
    }
    return HomeItem(
        id=request_id,
        kind=kind,
        title=title,
        status=raw.get("status"),
        status_label=raw.get("status"),
        date=raw.get("createdAt"),
        href=f"{_DETAIL_HREF}/{request_id}",
        source=_SYSTEM,
        meta=meta,
    )


class _PrcSource:
    """Adapter: ``ProductRegistrationService.list_requests`` → SectionFetch."""

    system = _SYSTEM
    endpoint = _ENDPOINT
    _kind = "request"
    _own_scope = False

    def __init__(self, service_factory: Callable[[], Any]) -> None:
        self._service_factory = service_factory

    async def fetch(self, ctx: HomeSourceContext, *, limit: int) -> SectionFetch:
        actor = PrcActor(
            user_id=ctx.user_id,
            permissions=ctx.permissions,
            is_superadmin=ctx.is_superadmin,
            channel="portal",
        )
        try:
            data = await asyncio.to_thread(
                self._service_factory().list_requests,
                actor=actor,
                filters={"page": 1, "pageSize": limit},
                own_scope=self._own_scope,
            )
        except PrcForbiddenError:
            return SectionFetch(
                status="forbidden",
                message="Acesso negado pelo domínio PRC.",
            )
        except Exception:  # pragma: no cover - defesa residual
            logger.warning(
                "prc_home_source_unexpected_error kind=%s",
                self._kind,
                exc_info=True,
            )
            return SectionFetch(status="unavailable", reason="upstream_error")

        if not isinstance(data, dict) or not isinstance(
            data.get("items"), list
        ):
            return SectionFetch(status="unavailable", reason="contract_error")

        try:
            items = tuple(
                _map_prc_item(raw, kind=self._kind)
                for raw in data["items"]
            )
        except ValueError:
            return SectionFetch(status="unavailable", reason="contract_error")

        total = data.get("total") if isinstance(data.get("total"), int) else None
        if not items:
            return SectionFetch(status="empty", total=total or 0)
        return SectionFetch(status="available", items=items, total=total)


class PrcQueueHomeSource(_PrcSource):
    """``tasks`` — fila PRC que o ator tem capacidade de atender."""

    _kind = "task"
    _own_scope = False


class PrcMineHomeSource(_PrcSource):
    """``requests`` — casos PRC do próprio solicitante."""

    _kind = "request"
    _own_scope = True
