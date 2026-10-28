"""Rota da Visão geral do Portal Engenharia (F3.OVERVIEW).

`GET /v1/overview` — composição autorizada dos seis indicadores
oficiais (3 LMP + 3 TRANSFORMA+) com metas/IDD dos owners. AuthZ:
- `require_any_permission(["engineering.access"])` — permissão efetiva
  resolvida pela Core via delpi_auth (fail-closed).
- `principal_type == "user"` — página personalizada; service
  principals não recebem Overview.
AuthZ por recurso permanece nos owners downstream: Bearer humano é
delegado e 401/403 viram `forbidden` por família, sem fallback
privilegiado (correção F2a.R1 preservada).

Filtros (query, opcionais — semântica oficial do dashboard):
- `start_date` / `end_date` YYYY-MM-DD (intervalo válido);
- `competence` YYYY-MM (informativa para SI quando o intervalo cruza
  meses — as datas são o contrato efetivo das fontes operacionais);
- `branch` — unidade operacional para indicadores cujo owner suporta;
  scores SI consolidados permanecem consolidados.
"""

from __future__ import annotations

import re

from fastapi import APIRouter, Query

from delpi_auth.authorization import require_any_permission
from delpi_auth.context_resolver import resolve_user_context

from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.application.ports.overview_sources import OverviewQuery
from engineering_app.composition.overview_composer import (
    build_get_engineering_overview_use_case,
)
from engineering_app.core.responses import fail, ok
from engineering_app.middleware.request_observability_middleware import (
    get_request_id,
)

router = APIRouter()

ENGINEERING_ACCESS = "engineering.access"
_OPERATION_ID = "get_engineering_overview"

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_COMPETENCE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _valid_filters(
    start_date: str | None,
    end_date: str | None,
    competence: str | None,
) -> str | None:
    """Retorna mensagem de erro ou None quando válido."""
    for name, value in (("start_date", start_date), ("end_date", end_date)):
        if value is not None and not _ISO_DATE_RE.match(value.strip()):
            return f"{name} inválida — use YYYY-MM-DD."
    if (
        start_date
        and end_date
        and _ISO_DATE_RE.match(start_date.strip())
        and _ISO_DATE_RE.match(end_date.strip())
        and start_date.strip() > end_date.strip()
    ):
        return "start_date não pode ser posterior a end_date."
    if competence is not None and not _COMPETENCE_RE.match(competence.strip()):
        return "competence inválida — use YYYY-MM."
    return None


@router.get(
    "/v1/overview",
    operation_id="get_engineering_overview",
    summary="Visão geral — seis indicadores oficiais de Engenharia",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_engineering_overview(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    competence: str | None = Query(default=None),
    branch: str | None = Query(default=None),
):
    user = resolve_user_context()

    if getattr(user, "principal_type", None) != "user":
        return fail(
            "A Visão geral personalizada exige principal humano.",
            403,
            operation_id=_OPERATION_ID,
        )

    error = _valid_filters(start_date, end_date, competence)
    if error:
        return fail(error, 400, operation_id=_OPERATION_ID)

    query = OverviewQuery(
        start_date=start_date.strip() if start_date else None,
        end_date=end_date.strip() if end_date else None,
        competence=competence.strip() if competence else None,
        branch=branch.strip() if branch else None,
    )
    ctx = HomeSourceContext(
        user_id=str(getattr(user, "id", "") or ""),
        access_token=str(getattr(user, "access_token", "") or ""),
        request_id=get_request_id(),
    )
    overview = await build_get_engineering_overview_use_case().execute(
        ctx, query=query
    )
    return ok(
        overview.model_dump(),
        message="Visão geral do Portal Engenharia.",
        operation_id=_OPERATION_ID,
    )
