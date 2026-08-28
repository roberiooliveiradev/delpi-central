from __future__ import annotations

from fastapi import APIRouter, Query, Request

from production_control_app.composition.pc_composer import build_overview_service
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import BranchAccessDenied, DelpiGatewayError, InvalidBranch
from production_control_app.interface.http.auth_http import resolve_user

router = APIRouter(tags=["Overview"])


@router.get("/overview")
def get_overview(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    volumeView: str = Query(
        "day",
        description="Visualização do volume: day (mês corrente) ou month_yoy (mês × ano anterior)",
    ),
    startDate: str | None = Query(
        None,
        description="Início do período (YYYY-MM-DD). Omitido = 1º dia do mês corrente.",
    ),
    endDate: str | None = Query(
        None,
        description="Fim do período (YYYY-MM-DD). Omitido = hoje no fuso operacional.",
    ),
):
    user = resolve_user(request)
    try:
        data = build_overview_service().build(
            user,
            branch=branch,
            volume_view=volumeView,
            start_date=startDate,
            end_date=endDate,
        )
    except InvalidBranch as exc:
        return fail(str(exc), 422)
    except BranchAccessDenied as exc:
        return fail(str(exc), 403)
    except PermissionError as exc:
        return fail(str(exc), 403)
    except DelpiGatewayError as exc:
        return fail(str(exc), 502)
    return ok(data)
