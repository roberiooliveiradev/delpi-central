"""Rotas funcionais LMP da Engineering API (G3 — contratos E-LMP-01/03).

`GET /v1/lmps` — listagem funcional com itens enriquecidos pelas regras
de Engenharia (R01–R12) sobre facts oficiais da api-delpi.
`GET /v1/lmps/summary` — KPIs realizados (sem metas/IDD — owner: SI).

AuthZ unificada (diretriz G3): exclusivamente `engineering.access`,
resolvida pela Core via delpi_auth — fail-closed. Nenhuma permissão
legada (`api-delpi.access`, `dashboard-*.view`) é exigida ou aceita como
substituta nestes contratos; `caller_app` nunca é autoridade.

Estado honesto: indisponibilidade da fonte facts propaga como
`status=unavailable|forbidden` no payload — nunca lista vazia falsa.
"""

from __future__ import annotations

import re

from fastapi import APIRouter, Query

from delpi_auth.authorization import require_any_permission
from delpi_auth.context_resolver import resolve_user_context

from engineering_app.application.models.lmp import LmpQuery
from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.composition.lmp_composer import (
    build_delegated_auxiliary_source,
    build_get_lmp_detail_use_case,
    build_get_lmp_history_use_case,
    build_get_lmp_summary_use_case,
    build_list_lmps_dashboard_use_case,
)
from engineering_app.core.responses import fail, ok
from engineering_app.middleware.request_observability_middleware import (
    get_request_id,
)

router = APIRouter()

ENGINEERING_ACCESS = "engineering.access"

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MAX_PAGE_SIZE = 500


def _source_context(user) -> HomeSourceContext:
    return HomeSourceContext(
        user_id=str(getattr(user, "id", "") or ""),
        access_token=str(getattr(user, "access_token", "") or ""),
        request_id=get_request_id(),
    )


def _require_human_principal(operation_id: str):
    user = resolve_user_context()
    if getattr(user, "principal_type", None) != "user":
        return None, fail(
            "Consulta personalizada de LMPs exige principal humano.",
            403,
            operation_id=operation_id,
        )
    return user, None


def _validate_period(
    start_date: str | None, end_date: str | None
) -> str | None:
    for name, value in (("start_date", start_date), ("end_date", end_date)):
        if value is not None and not _ISO_DATE_RE.match(value.strip()):
            return f"{name} inválida — use YYYY-MM-DD."
    if (
        start_date
        and end_date
        and start_date.strip() > end_date.strip()
    ):
        return "start_date não pode ser posterior a end_date."
    return None


@router.get(
    "/v1/lmps",
    operation_id="list_lmps",
    summary="Listagem funcional de LMPs — regras Engineering API",
)
@require_any_permission([ENGINEERING_ACCESS])
async def list_lmps(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    listing_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=_MAX_PAGE_SIZE),
):
    user, denied = _require_human_principal("list_lmps")
    if denied is not None:
        return denied

    error = _validate_period(start_date, end_date)
    if error:
        return fail(error, 400, operation_id="list_lmps")

    query = LmpQuery(
        start_date=start_date.strip() if start_date else None,
        end_date=end_date.strip() if end_date else None,
        branch=branch.strip() if branch else None,
        listing_type=listing_type.strip() if listing_type else None,
        status_filter=status.strip() if status else None,
        page=page,
        page_size=page_size,
    )
    try:
        result = await build_list_lmps_dashboard_use_case().execute(
            _source_context(user), query
        )
    except ValueError as exc:
        return fail(str(exc), 400, operation_id="list_lmps")

    if result.get("status") == "forbidden":
        return fail(
            "Acesso negado pelo owner da fonte.", 403, operation_id="list_lmps"
        )
    return ok(
        result,
        message="LMPs carregadas com sucesso.",
        operation_id="list_lmps",
    )


@router.get(
    "/v1/lmps/summary",
    operation_id="get_lmp_summary",
    summary="KPIs realizados de LMP — sem metas/IDD",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_lmp_summary(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    branch: str | None = Query(default=None),
):
    user, denied = _require_human_principal("get_lmp_summary")
    if denied is not None:
        return denied

    error = _validate_period(start_date, end_date)
    if error:
        return fail(error, 400, operation_id="get_lmp_summary")

    query = LmpQuery(
        start_date=start_date.strip() if start_date else None,
        end_date=end_date.strip() if end_date else None,
        branch=branch.strip() if branch else None,
    )
    try:
        result = await build_get_lmp_summary_use_case().execute(
            _source_context(user), query
        )
    except ValueError as exc:
        return fail(str(exc), 400, operation_id="get_lmp_summary")

    if result.get("status") == "forbidden":
        return fail(
            "Acesso negado pelo owner da fonte.",
            403,
            operation_id="get_lmp_summary",
        )
    return ok(
        result,
        message="Resumo realizado de LMPs carregado com sucesso.",
        operation_id="get_lmp_summary",
    )


def _lmp_result_to_response(result: dict, operation_id: str, not_found_message: str):
    """Mapeia estados honestos da fonte para HTTP sem inventar payload."""
    status = result.get("status")
    if status == "forbidden":
        return fail(
            "Acesso negado pelo owner da fonte.", 403, operation_id=operation_id
        )
    if status == "not_found":
        return fail(not_found_message, 404, operation_id=operation_id)
    return ok(result, message="Consulta realizada com sucesso.", operation_id=operation_id)


# --- READs delegados aos owners oficiais (G5) ------------------------------
# Metas/IDD → Strategic Indicators; streak NC → owner NC; Bearer humano
# delegado — 401/403 downstream viram estado `forbidden` honesto.


@router.get(
    "/v1/lmps/goal-context",
    operation_id="get_lmp_goal_context",
    summary="Contexto de metas (SI) do dashboard LMP — delegação ao owner",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_lmp_goal_context(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    branch: str | None = Query(default=None),
):
    user, denied = _require_human_principal("get_lmp_goal_context")
    if denied is not None:
        return denied

    error = _validate_period(start_date, end_date)
    if error:
        return fail(error, 400, operation_id="get_lmp_goal_context")

    result = await build_delegated_auxiliary_source().fetch_goal_context(
        _source_context(user),
        start_date=start_date.strip() if start_date else None,
        end_date=end_date.strip() if end_date else None,
        branch=branch.strip() if branch else None,
    )
    if result.get("status") == "forbidden":
        return fail(
            "Acesso negado pelo owner de metas.",
            403,
            operation_id="get_lmp_goal_context",
        )
    return ok(
        result,
        message="Contexto de metas carregado.",
        operation_id="get_lmp_goal_context",
    )


@router.get(
    "/v1/lmps/department-idd",
    operation_id="get_lmp_department_idd",
    summary="Nota IDD do departamento engineering (SI) — delegação ao owner",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_lmp_department_idd(
    competence: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    branch: str | None = Query(default=None),
):
    user, denied = _require_human_principal("get_lmp_department_idd")
    if denied is not None:
        return denied

    error = _validate_period(start_date, end_date)
    if error:
        return fail(error, 400, operation_id="get_lmp_department_idd")

    result = await build_delegated_auxiliary_source().fetch_department_idd(
        _source_context(user),
        competence=competence.strip() if competence else None,
        start_date=start_date.strip() if start_date else None,
        end_date=end_date.strip() if end_date else None,
        branch=branch.strip() if branch else None,
    )
    if result.get("status") == "forbidden":
        return fail(
            "Acesso negado pelo owner de IDD.",
            403,
            operation_id="get_lmp_department_idd",
        )
    return ok(
        result,
        message="IDD departamental carregado.",
        operation_id="get_lmp_department_idd",
    )


@router.get(
    "/v1/lmps/nonconformities/streak",
    operation_id="get_lmp_nc_streak",
    summary="Dias sem NC (owner NC) — delegação ao owner, sem escrita",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_lmp_nc_streak():
    user, denied = _require_human_principal("get_lmp_nc_streak")
    if denied is not None:
        return denied

    result = await build_delegated_auxiliary_source().fetch_nc_streak(
        _source_context(user)
    )
    if result.get("status") == "forbidden":
        return fail(
            "Acesso negado pelo owner de não conformidades.",
            403,
            operation_id="get_lmp_nc_streak",
        )
    return ok(
        result,
        message="Streak de dias sem NC carregado.",
        operation_id="get_lmp_nc_streak",
    )


@router.get(
    "/v1/lmps/{sale_number}/history/events",
    operation_id="get_lmp_history_events",
    summary="Histórico de eventos da OV — regras Engineering API",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_lmp_history_events(
    sale_number: str,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    revision: str | None = Query(default=None),
):
    user, denied = _require_human_principal("get_lmp_history_events")
    if denied is not None:
        return denied

    error = _validate_period(start_date, end_date)
    if error:
        return fail(error, 400, operation_id="get_lmp_history_events")

    query = LmpQuery(
        sale_number=sale_number.strip(),
        start_date=start_date.strip() if start_date else None,
        end_date=end_date.strip() if end_date else None,
        branch=branch.strip() if branch else None,
        revision=revision.strip() if revision else None,
    )
    result = await build_get_lmp_history_use_case(view="events").execute(
        _source_context(user), query
    )
    return _lmp_result_to_response(
        result, "get_lmp_history_events", "OV não encontrada na listagem de engenharia."
    )


@router.get(
    "/v1/lmps/{sale_number}/history/flow",
    operation_id="get_lmp_history_flow",
    summary="Fluxo de transições da OV — regras Engineering API",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_lmp_history_flow(
    sale_number: str,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    revision: str | None = Query(default=None),
):
    user, denied = _require_human_principal("get_lmp_history_flow")
    if denied is not None:
        return denied

    error = _validate_period(start_date, end_date)
    if error:
        return fail(error, 400, operation_id="get_lmp_history_flow")

    query = LmpQuery(
        sale_number=sale_number.strip(),
        start_date=start_date.strip() if start_date else None,
        end_date=end_date.strip() if end_date else None,
        branch=branch.strip() if branch else None,
        revision=revision.strip() if revision else None,
    )
    result = await build_get_lmp_history_use_case(view="flow").execute(
        _source_context(user), query
    )
    return _lmp_result_to_response(
        result, "get_lmp_history_flow", "OV não encontrada na listagem de engenharia."
    )


@router.get(
    "/v1/lmps/{sale_number}",
    operation_id="get_lmp_detail",
    summary="Detalhe funcional da OV/LMP — regras Engineering API",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_lmp_detail(
    sale_number: str,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    branch: str | None = Query(default=None),
):
    user, denied = _require_human_principal("get_lmp_detail")
    if denied is not None:
        return denied

    error = _validate_period(start_date, end_date)
    if error:
        return fail(error, 400, operation_id="get_lmp_detail")

    query = LmpQuery(
        sale_number=sale_number.strip(),
        start_date=start_date.strip() if start_date else None,
        end_date=end_date.strip() if end_date else None,
        branch=branch.strip() if branch else None,
    )
    result = await build_get_lmp_detail_use_case().execute(
        _source_context(user), query
    )
    return _lmp_result_to_response(
        result, "get_lmp_detail", "OV não encontrada na listagem de engenharia."
    )
