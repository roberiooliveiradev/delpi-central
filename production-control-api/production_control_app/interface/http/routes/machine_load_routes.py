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
        description="Recorte de leitura: entrega do PA a partir de (YYYY-MM-DD)",
    ),
    end_date: str | None = Query(
        default=None,
        alias="endDate",
        description="Recorte de leitura: entrega do PA até (YYYY-MM-DD)",
    ),
):
    """Fila congelada da filial. As datas só recortam a leitura — não puxam o TOTVS."""
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
        description="Entrega do PA a partir de (YYYY-MM-DD); vazio traz tudo que está atrasado",
    ),
    end_date: str | None = Query(
        default=None,
        alias="endDate",
        description="Entrega do PA até (YYYY-MM-DD); default hoje + 14 dias",
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
    body: SequenceReorderBody = Body(...),
):
    """Persiste a ordem manual das operações de um centro de trabalho no snapshot."""
    user = resolve_user(request)
    try:
        data = build_machine_load_service().reorder_sequence(
            user,
            branch=branch,
            work_center=work_center,
            ordered_keys=[item.model_dump() for item in body.ordered_keys],
        )
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(data, message="Sequência da carga máquina salva.")


@router.post("/machine-load/prioritize")
def prioritize_machine_load_conjunto(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    order_number: str = Query(
        ...,
        alias="orderNumber",
        min_length=6,
        max_length=30,
        description="Conjunto (C2_NUM) ou OP completa — os 6 primeiros dígitos definem o conjunto",
    ),
    work_center: str | None = Query(
        default=None,
        alias="workCenter",
        description="Centro de trabalho que continua ativo na resposta",
    ),
):
    """Leva todas as OPs do conjunto ao topo da fila de cada centro, sem ultrapassar ops já iniciadas."""
    user = resolve_user(request)
    try:
        data = build_machine_load_service().prioritize_conjunto(
            user,
            branch=branch,
            order_number=order_number,
            work_center=work_center,
        )
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(data, message=data.get("prioritization", {}).get("message"))


@router.post("/machine-load/optimize-delivery")
def optimize_machine_load_delivery_sequence(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    work_center: str | None = Query(
        default=None,
        alias="workCenter",
        description="Centro de trabalho que continua ativo na resposta",
    ),
):
    """Resequencia a fila de todos os centros pela entrega do PA, sem ultrapassar ops já iniciadas."""
    user = resolve_user(request)
    try:
        data = build_machine_load_service().optimize_delivery_sequence(
            user,
            branch=branch,
            work_center=work_center,
        )
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(data, message=data.get("optimization", {}).get("message"))


@router.post("/machine-load/withdraw")
def withdraw_machine_load_conjunto(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    order_number: str = Query(
        ...,
        alias="orderNumber",
        min_length=6,
        max_length=30,
        description="Conjunto (C2_NUM) ou OP completa — os 6 primeiros dígitos definem o conjunto",
    ),
    work_center: str | None = Query(
        default=None,
        alias="workCenter",
        description="Centro de trabalho que continua ativo na resposta",
    ),
):
    """Retira o conjunto da programação: some da fila de todos os centros e do cockpit público."""
    user = resolve_user(request)
    try:
        data = build_machine_load_service().withdraw_conjunto(
            user,
            branch=branch,
            order_number=order_number,
            work_center=work_center,
        )
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(data, message=data.get("withdrawal", {}).get("message"))


@router.post("/machine-load/restore")
def restore_machine_load_conjunto(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    order_number: str = Query(
        ...,
        alias="orderNumber",
        min_length=6,
        max_length=30,
        description="Conjunto (C2_NUM) retirado que volta para a fila",
    ),
    work_center: str | None = Query(
        default=None,
        alias="workCenter",
        description="Centro de trabalho que continua ativo na resposta",
    ),
):
    """Devolve o conjunto retirado à fila, na posição original do snapshot."""
    user = resolve_user(request)
    try:
        data = build_machine_load_service().restore_conjunto(
            user,
            branch=branch,
            order_number=order_number,
            work_center=work_center,
        )
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(data, message=data.get("withdrawal", {}).get("message"))


@router.post("/machine-load/transfer")
def transfer_machine_load_operation(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    production_order: str = Query(
        ...,
        alias="productionOrder",
        min_length=1,
        max_length=30,
        description="OP completa (H8_OP / C2_OP) da operação transferida",
    ),
    operation_code: str = Query(
        ...,
        alias="operationCode",
        min_length=1,
        max_length=10,
        description="Código da operação dentro da OP",
    ),
    target_work_center: str = Query(
        ...,
        alias="targetWorkCenter",
        min_length=1,
        max_length=20,
        description="Centro de trabalho de destino",
    ),
    work_center: str | None = Query(
        default=None,
        alias="workCenter",
        description="Centro de trabalho que continua ativo na resposta; vazio usa o destino",
    ),
):
    """Move a operação para o fim da fila de outro centro de trabalho."""
    user = resolve_user(request)
    try:
        data = build_machine_load_service().transfer_operation(
            user,
            branch=branch,
            production_order=production_order,
            operation_code=operation_code,
            target_work_center=target_work_center,
            work_center=work_center,
        )
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(data, message=data.get("transfer", {}).get("message"))


@router.post("/machine-load/transfer-set")
def transfer_machine_load_set(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    order_number: str = Query(
        ...,
        alias="orderNumber",
        min_length=6,
        max_length=30,
        description="C2_NUM do conjunto ou OP completa (usa o prefixo de 6 dígitos)",
    ),
    source_work_center: str = Query(
        ...,
        alias="sourceWorkCenter",
        min_length=1,
        max_length=20,
        description="Centro de trabalho de origem (só as OPs do conjunto neste CT saem)",
    ),
    target_work_center: str = Query(
        ...,
        alias="targetWorkCenter",
        min_length=1,
        max_length=20,
        description="Centro de trabalho de destino",
    ),
    work_center: str | None = Query(
        default=None,
        alias="workCenter",
        description="Centro de trabalho que continua ativo na resposta; vazio usa o destino",
    ),
):
    """Move as OPs do conjunto que estão no centro de origem para o destino."""
    user = resolve_user(request)
    try:
        data = build_machine_load_service().transfer_conjunto(
            user,
            branch=branch,
            order_number=order_number,
            source_work_center=source_work_center,
            target_work_center=target_work_center,
            work_center=work_center,
        )
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(data, message=data.get("transfer", {}).get("message"))


@router.get("/machine-load/locate")
def locate_machine_load(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    q: str = Query(
        ...,
        min_length=1,
        max_length=40,
        description="Conjunto (C2_NUM / OP completa) ou produto (PA)",
    ),
):
    """Rastreia conjunto (C2_NUM: todas as OPs com o mesmo prefixo de 6 dígitos) ou lista conjuntos do PA."""
    user = resolve_user(request)
    try:
        data = build_machine_load_service().locate(
            user,
            branch=branch,
            query=q,
        )
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(data)
