from __future__ import annotations

from fastapi import APIRouter, Body, Query, Request
from pydantic import BaseModel, Field

from production_control_app.composition.pc_composer import build_machine_load_service
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import (
    BranchAccessDenied,
    DelpiGatewayError,
    InvalidBranch,
    SnapshotNotFound,
)
from production_control_app.interface.http.auth_http import resolve_user

router = APIRouter(tags=["Machine load"])


class SequenceKeyBody(BaseModel):
    production_order: str = Field(..., min_length=1, max_length=30)
    operation_code: str = Field(..., min_length=1, max_length=10)


class SequenceReorderBody(BaseModel):
    ordered_keys: list[SequenceKeyBody] = Field(default_factory=list)


def _query_params(
    branch: str,
    work_center: str | None,
    start_date: str | None,
    end_date: str | None,
) -> dict[str, str | None]:
    return {
        "branch": branch,
        "work_center": work_center,
        "start_date": start_date,
        "end_date": end_date,
    }


def _handle_machine_load_errors(exc: Exception):
    if isinstance(exc, InvalidBranch):
        return fail(str(exc), 422)
    if isinstance(exc, BranchAccessDenied):
        return fail(str(exc), 403)
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403)
    if isinstance(exc, SnapshotNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, ValueError):
        return fail(str(exc), 422)
    if isinstance(exc, DelpiGatewayError):
        return fail(str(exc), 502)
    raise exc


@router.get("/machine-load")
def get_machine_load(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    work_center: str | None = Query(
        default=None,
        alias="workCenter",
        description="Centro de trabalho ativo; vazio usa o primeiro da lista",
    ),
    start_date: str | None = Query(
        default=None,
        alias="startDate",
        description="Início da janela programada (YYYY-MM-DD)",
    ),
    end_date: str | None = Query(
        default=None,
        alias="endDate",
        description="Fim da janela programada (YYYY-MM-DD)",
    ),
):
    user = resolve_user(request)
    try:
        data = build_machine_load_service().build(
            user,
            **_query_params(branch, work_center, start_date, end_date),
        )
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(data)


@router.post("/machine-load/refresh")
def refresh_machine_load(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    work_center: str | None = Query(
        default=None,
        alias="workCenter",
        description="Centro de trabalho ativo após o refresh",
    ),
    start_date: str | None = Query(
        default=None,
        alias="startDate",
        description="Início da janela programada (YYYY-MM-DD)",
    ),
    end_date: str | None = Query(
        default=None,
        alias="endDate",
        description="Fim da janela programada (YYYY-MM-DD)",
    ),
):
    """Regenera o snapshot congelado a partir do TOTVS (ação explícita do PCP)."""
    user = resolve_user(request)
    try:
        data = build_machine_load_service().refresh(
            user,
            **_query_params(branch, work_center, start_date, end_date),
        )
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(data, message="Carga máquina atualizada com os dados do TOTVS.")


@router.patch("/machine-load/sequence")
def patch_machine_load_sequence(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    work_center: str = Query(
        ...,
        alias="workCenter",
        description="Centro de trabalho cuja sequência será reordenada",
    ),
    start_date: str | None = Query(
        default=None,
        alias="startDate",
        description="Início da janela programada (YYYY-MM-DD)",
    ),
    end_date: str | None = Query(
        default=None,
        alias="endDate",
        description="Fim da janela programada (YYYY-MM-DD)",
    ),
    body: SequenceReorderBody = Body(...),
):
    """Persiste a ordem manual das operações de um centro de trabalho no snapshot."""
    user = resolve_user(request)
    try:
        data = build_machine_load_service().reorder_sequence(
            user,
            branch=branch,
            work_center=work_center,
            start_date=start_date,
            end_date=end_date,
            ordered_keys=[item.model_dump() for item in body.ordered_keys],
        )
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(data, message="Sequência da carga máquina salva.")
