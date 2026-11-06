from __future__ import annotations

import json
import logging
import queue
import threading
from collections.abc import Iterator
from typing import Any

from fastapi import APIRouter, Body, Path, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from production_control_app.composition.pc_composer import (
    build_line_feeder_service,
    build_line_feeder_urgent_requests_service,
)
from production_control_app.core.responses import fail, json_safe, ok
from production_control_app.domain.errors import (
    BranchAccessDenied,
    DelpiGatewayError,
    HorizonPreviewStale,
    InvalidBranch,
    OperatorFeedbackMaterialNotFound,
    OperatorFeedbackMaterialStateError,
    SnapshotNotFound,
)
from production_control_app.interface.http.auth_http import resolve_user

router = APIRouter(tags=["Line feeder"])
logger = logging.getLogger(__name__)


class PickPlanCreateBody(BaseModel):
    branch: str = Field(..., min_length=2, max_length=2)
    cutoff_date: str = Field(..., alias="cutoffDate", min_length=10, max_length=10)
    cutoff_time: str | None = Field(default=None, alias="cutoffTime", max_length=5)
    work_center: str | None = Field(default=None, alias="workCenter", max_length=40)

    model_config = {"populate_by_name": True}


class PickItemStatusBody(BaseModel):
    branch: str = Field(..., min_length=2, max_length=2)
    status: str = Field(..., min_length=1, max_length=16)

    model_config = {"populate_by_name": True}


class PickPlanCloseBody(BaseModel):
    branch: str = Field(..., min_length=2, max_length=2)

    model_config = {"populate_by_name": True}


def _line_feeder_error_status(exc: Exception) -> int | None:
    if isinstance(exc, InvalidBranch):
        return 422
    if isinstance(exc, BranchAccessDenied):
        return 403
    if isinstance(exc, PermissionError):
        return 403
    if isinstance(exc, SnapshotNotFound):
        return 404
    if isinstance(exc, OperatorFeedbackMaterialNotFound):
        return 404
    if isinstance(exc, OperatorFeedbackMaterialStateError):
        return 409
    if isinstance(exc, HorizonPreviewStale):
        return 409
    if isinstance(exc, LookupError):
        return 404
    if isinstance(exc, ValueError):
        return 422
    if isinstance(exc, DelpiGatewayError):
        return 502
    return None


def _handle_line_feeder_errors(exc: Exception):
    status = _line_feeder_error_status(exc)
    if status is None:
        raise exc
    return fail(str(exc), status)


def _sse_data(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(json_safe(payload), ensure_ascii=False)}\n\n"


def _materials_preview_error_event(exc: Exception) -> dict[str, Any]:
    status = _line_feeder_error_status(exc)
    if status is None:
        logger.exception("line_feeder materials preview stream failed")
        return {
            "type": "error",
            "message": "Não foi possível calcular a necessidade de materiais.",
            "status": 500,
        }
    return {"type": "error", "message": str(exc), "status": status}


class HorizonPreviewBody(BaseModel):
    branch: str = Field(..., min_length=2, max_length=2)
    work_centers: list[str] = Field(..., alias="workCenters", min_length=1)
    hours_per_work_center: float = Field(..., alias="hoursPerWorkCenter", gt=0)

    model_config = {"populate_by_name": True}


@router.post(
    "/line-feeder/horizon/preview",
    operation_id="preview_line_feeder_horizon",
)
def preview_line_feeder_horizon(
    request: Request,
    body: HorizonPreviewBody = Body(...),
):
    """Prévia do horizonte de produção por CT — somente leitura, sem persistência.

    Orçamento ``hoursPerWorkCenter`` aplica-se **a cada** centro selecionado.
    Sequência: fila PUBLISHED. Saldos vivos + tempo padrão canônico (api-delpi).
    """
    user = resolve_user(request)
    try:
        data = build_line_feeder_service().preview_horizon(
            user,
            branch=body.branch,
            work_centers=body.work_centers,
            hours_per_work_center=body.hours_per_work_center,
        )
    except Exception as exc:
        return _handle_line_feeder_errors(exc)
    return ok(data)


@router.post(
    "/line-feeder/materials/preview",
    operation_id="preview_line_feeder_materials",
)
def preview_line_feeder_materials(
    request: Request,
    body: HorizonPreviewBody = Body(...),
):
    """Prévia dinâmica de materiais do horizonte — somente leitura.

    ``to_collect = max(0, necessidade − saldo do ponto de uso)``. Não persiste
    lista, não usa status de coleta e não desconta o almoxarifado como se já
    estivesse na fábrica.
    """
    user = resolve_user(request)
    try:
        data = build_line_feeder_service().preview_materials(
            user,
            branch=body.branch,
            work_centers=body.work_centers,
            hours_per_work_center=body.hours_per_work_center,
        )
    except Exception as exc:
        return _handle_line_feeder_errors(exc)
    return ok(data)


@router.post(
    "/line-feeder/materials/preview/stream",
    operation_id="preview_line_feeder_materials_stream",
)
def preview_line_feeder_materials_stream(
    request: Request,
    body: HorizonPreviewBody = Body(...),
):
    """Prévia de materiais com progresso SSE (progress* → result | error).

    Mesmo body/auth do POST síncrono. O POST legado permanece para compat.
    """
    user = resolve_user(request)
    service = build_line_feeder_service()
    branch = body.branch
    work_centers = list(body.work_centers)
    hours = body.hours_per_work_center

    def event_stream() -> Iterator[str]:
        # Thread + queue: progresso em tempo real sem bloquear o ASGI loop.
        # out.get SEM timeout trava o TestClient (e o cliente) se o worker
        # morrer sem emitir "done" — por isso poll com timeout + join cuidadoso.
        out: queue.Queue[tuple[str, Any]] = queue.Queue()
        get_timeout_s = 1.0

        def on_progress(event: dict[str, Any]) -> None:
            out.put(("progress", event))

        def worker() -> None:
            try:
                data = service.preview_materials(
                    user,
                    branch=branch,
                    work_centers=work_centers,
                    hours_per_work_center=hours,
                    on_progress=on_progress,
                )
                out.put(("result", data))
            except Exception as exc:  # noqa: BLE001 — mapeado para evento error
                out.put(("error", exc))
            finally:
                out.put(("done", None))

        thread = threading.Thread(
            target=worker,
            name="line-feeder-materials-preview-stream",
            daemon=True,
        )
        thread.start()
        try:
            while True:
                try:
                    kind, payload = out.get(timeout=get_timeout_s)
                except queue.Empty:
                    if thread.is_alive():
                        continue
                    # Worker morreu sem "done" (não deveria) — encerra o stream.
                    yield _sse_data(
                        {
                            "type": "error",
                            "message": "Não foi possível calcular a necessidade de materiais.",
                            "status": 500,
                        }
                    )
                    break
                if kind == "done":
                    break
                if kind == "progress" and isinstance(payload, dict):
                    yield _sse_data(payload)
                elif kind == "result":
                    yield _sse_data({"type": "result", "data": payload})
                elif kind == "error" and isinstance(payload, Exception):
                    yield _sse_data(_materials_preview_error_event(payload))
        finally:
            # Não bloqueia o teardown do TestClient/ASGI se o worker ainda roda.
            thread.join(timeout=1.0)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/line-feeder/published-queue",
    operation_id="get_line_feeder_published_queue",
)
def get_line_feeder_published_queue(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    work_center: str | None = Query(
        default=None,
        alias="workCenter",
        description="Recorte opcional por centro de trabalho; vazio = todos os postos da filial",
    ),
):
    """Fila PUBLISHED na ordem do operador — fundação do Alimentador (somente leitura).

    Fonte: ``machine_load_publications``. Sem fallback para WORKING, sem refresh
    e sem reordenação por horário TOTVS. Revisão efetiva: ``publication_revision``
    (derivada de ``row_version``/xmin), sensível a mutações LIVE.
    """
    user = resolve_user(request)
    try:
        data = build_line_feeder_service().get_published_queue(
            user,
            branch=branch,
            work_center=work_center,
        )
    except Exception as exc:
        return _handle_line_feeder_errors(exc)
    return ok(data)


@router.get("/line-feeder/requirements")
def get_line_feeder_requirements(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    cutoff_date: str = Query(
        ...,
        alias="cutoffDate",
        description="Data do corte (YYYY-MM-DD)",
    ),
    cutoff_time: str | None = Query(
        default=None,
        alias="cutoffTime",
        description="Hora do corte (HH:MM); vazio considera o dia inteiro",
    ),
    work_center: str | None = Query(
        default=None,
        alias="workCenter",
        description="Recorte por bancada; o rateio do saldo continua global",
    ),
    status: str | None = Query(
        default=None,
        description="covered, to_pick, at_risk, unknown ou all",
    ),
    refresh: bool = Query(False, description="Ignora o cache e relê a api-delpi"),
):
    """Material que precisa estar nas bancadas até o horário do corte."""
    user = resolve_user(request)
    try:
        data = build_line_feeder_service().get_requirements(
            user,
            branch=branch,
            cutoff_date=cutoff_date,
            cutoff_time=cutoff_time,
            work_center=work_center,
            status=status,
            refresh=refresh,
        )
    except Exception as exc:
        return _handle_line_feeder_errors(exc)
    return ok(data)


@router.get("/line-feeder/products/{code}")
def get_line_feeder_product_detail(
    request: Request,
    code: str = Path(..., min_length=1, description="Código do produto"),
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    cutoff_date: str = Query(
        ...,
        alias="cutoffDate",
        description="Data do corte (YYYY-MM-DD)",
    ),
    cutoff_time: str | None = Query(
        default=None,
        alias="cutoffTime",
        description="Hora do corte (HH:MM); vazio considera o dia inteiro",
    ),
):
    """Identidade, saldo do almoxarifado, bancadas do corte e transferências recentes."""
    user = resolve_user(request)
    try:
        data = build_line_feeder_service().get_product_detail(
            user,
            product_code=code,
            branch=branch,
            cutoff_date=cutoff_date,
            cutoff_time=cutoff_time,
        )
    except Exception as exc:
        return _handle_line_feeder_errors(exc)
    return ok(data)


@router.post("/line-feeder/pick-plans")
def create_line_feeder_pick_plan(
    request: Request,
    body: PickPlanCreateBody = Body(...),
):
    """Congela o que falta entregar no corte como lista de coleta."""
    user = resolve_user(request)
    try:
        data = build_line_feeder_service().create_pick_plan(
            user,
            branch=body.branch,
            cutoff_date=body.cutoff_date,
            cutoff_time=body.cutoff_time,
            work_center=body.work_center,
        )
    except Exception as exc:
        return _handle_line_feeder_errors(exc)
    return ok(data)


@router.get("/line-feeder/pick-plans")
def list_line_feeder_pick_plans(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    status: str | None = Query(default=None, description="open ou closed"),
    limit: int = Query(50, ge=1, le=200),
):
    user = resolve_user(request)
    try:
        data = build_line_feeder_service().list_pick_plans(
            user,
            branch=branch,
            status=status,
            limit=limit,
        )
    except Exception as exc:
        return _handle_line_feeder_errors(exc)
    return ok(data)


@router.get("/line-feeder/pick-plans/{plan_id}")
def get_line_feeder_pick_plan(
    request: Request,
    plan_id: str = Path(..., description="Identificador da lista de coleta"),
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
):
    user = resolve_user(request)
    try:
        data = build_line_feeder_service().get_pick_plan(
            user,
            branch=branch,
            plan_id=plan_id,
        )
    except Exception as exc:
        return _handle_line_feeder_errors(exc)
    return ok(data)


@router.patch("/line-feeder/pick-plans/{plan_id}/items/{item_id}")
def update_line_feeder_pick_item(
    request: Request,
    plan_id: str = Path(..., description="Identificador da lista de coleta"),
    item_id: str = Path(..., description="Identificador do item"),
    body: PickItemStatusBody = Body(...),
):
    """Avança ou volta o item: pending, picked ou delivered."""
    user = resolve_user(request)
    try:
        data = build_line_feeder_service().update_pick_item_status(
            user,
            branch=body.branch,
            plan_id=plan_id,
            item_id=item_id,
            status=body.status,
        )
    except Exception as exc:
        return _handle_line_feeder_errors(exc)
    return ok(data)


@router.post("/line-feeder/pick-plans/{plan_id}/close")
def close_line_feeder_pick_plan(
    request: Request,
    plan_id: str = Path(..., description="Identificador da lista de coleta"),
    body: PickPlanCloseBody = Body(...),
):
    user = resolve_user(request)
    try:
        data = build_line_feeder_service().close_pick_plan(
            user,
            branch=body.branch,
            plan_id=plan_id,
        )
    except Exception as exc:
        return _handle_line_feeder_errors(exc)
    return ok(data)


class UrgentMaterialStatusBody(BaseModel):
    branch: str = Field(..., min_length=2, max_length=2)
    status: str = Field(..., min_length=1, max_length=16)

    model_config = {"populate_by_name": True}


@router.get("/line-feeder/operator-feedback-requests")
def list_urgent_feedback_requests(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
):
    """Solicitações urgentes das bancadas — materiais faltantes informados
    pelo operador via Operator Feedback (C5). Fila própria: não são pick
    plans e não viram lista de coleta automaticamente."""
    user = resolve_user(request)
    try:
        data = build_line_feeder_urgent_requests_service().list_requests(
            user, branch=branch
        )
    except Exception as exc:
        return _handle_line_feeder_errors(exc)
    return ok(data)


@router.patch("/line-feeder/operator-feedback-materials/{material_id}")
def update_urgent_feedback_material(
    request: Request,
    material_id: str = Path(..., description="Identificador do material"),
    body: UrgentMaterialStatusBody = Body(...),
):
    """pending -> picked -> delivered. A filial autorizada é a do registro —
    o body.branch é conferido como contexto, mas nunca é autoridade."""
    user = resolve_user(request)
    try:
        data = build_line_feeder_urgent_requests_service().update_material_status(
            user,
            material_id=material_id,
            status=body.status,
        )
    except Exception as exc:
        return _handle_line_feeder_errors(exc)
    return ok(data)
