"""Cockpit público do operador — leitura anônima da fila e aviso de mudança em tempo real."""

from __future__ import annotations

from fastapi import APIRouter, Header, Query, WebSocket, WebSocketException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from production_control_app.application.services.machine_load_realtime_hub import (
    machine_load_realtime_hub,
)
from production_control_app.composition.pc_composer import (
    build_branch_access_service,
    build_machine_load_service,
    build_production_run_service,
    build_public_cockpit_access_service,
    build_public_machine_load_drawing_service,
    build_public_machine_load_product_model_service,
    build_public_operation_appointments_service,
    build_public_operation_materials_service,
    build_public_operation_process_inspections_service,
    build_public_work_center_downtime_items_service,
    build_public_work_center_performance_service,
)
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import (
    BenchSessionRequired,
    DelpiGatewayError,
    DrawingNotFound,
    DrawingSourceUnavailable,
    InvalidBranch,
    Product3DModelNotFound,
    ProductionRunConflict,
    ProductionRunNotFound,
    PublicAccessDenied,
    PulseDeviceUnavailable,
    PulseGatewayError,
    SnapshotNotFound,
)
from production_control_app.interface.http.drawing_response import drawing_pdf_response

router = APIRouter(prefix="/public/machine-load", tags=["Public machine load"])

_BENCH_SESSION_HEADER = "X-Delpi-Bench-Session"


class BenchSessionBody(BaseModel):
    model_config = {"populate_by_name": True}

    branch: str = Field(..., min_length=2, max_length=2)
    work_center: str = Field(..., alias="workCenter", min_length=1, max_length=40)
    operator_code: str = Field(..., alias="operatorCode", min_length=1, max_length=40)
    operator_name: str | None = Field(default=None, alias="operatorName", max_length=120)
    website: str | None = None  # honeypot


class StartRunBody(BaseModel):
    model_config = {"populate_by_name": True}

    branch: str = Field(..., min_length=2, max_length=2)
    work_center: str = Field(..., alias="workCenter", min_length=1, max_length=40)
    production_order: str = Field(..., alias="productionOrder", min_length=1, max_length=40)
    operation_code: str = Field(..., alias="operationCode", min_length=1, max_length=20)
    planned_qty: float | None = Field(default=None, alias="plannedQty")
    website: str | None = None  # honeypot


def _handle_public_errors(exc: Exception):
    if isinstance(exc, PublicAccessDenied):
        return fail(str(exc), 404)
    if isinstance(exc, InvalidBranch):
        return fail(str(exc), 422)
    if isinstance(exc, SnapshotNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, DrawingNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, DrawingSourceUnavailable):
        return fail(str(exc), 503)
    if isinstance(exc, Product3DModelNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, BenchSessionRequired):
        return fail(str(exc), 401)
    if isinstance(exc, ProductionRunConflict):
        return fail(str(exc), 409)
    if isinstance(exc, ProductionRunNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, PulseDeviceUnavailable):
        return fail(str(exc), 422)
    if isinstance(exc, PulseGatewayError):
        return fail(str(exc), 502)
    if isinstance(exc, ValueError):
        return fail(str(exc), 422)
    if isinstance(exc, DelpiGatewayError):
        return fail(str(exc), 502)
    raise exc


def _assert_cockpit_token(token: str):
    if not build_public_cockpit_access_service().is_valid_token(token):
        return fail("Link do cockpit inválido ou desativado.", 404)
    return None


def _honeypot_ok(website: str | None) -> bool:
    return not str(website or "").strip()


@router.get("/{token}")
def get_public_machine_load(
    token: str,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    work_center: str | None = Query(
        default=None,
        alias="workCenter",
        description="Centro de trabalho do operador; vazio lista apenas os postos",
    ),
):
    """Fila congelada do posto, somente leitura (sem seed do TOTVS e sem identidade do PCP)."""
    if not build_public_cockpit_access_service().is_valid_token(token):
        return fail("Link do cockpit inválido ou desativado.", 404)
    try:
        data = build_machine_load_service().build_public(
            branch=branch,
            work_center=work_center,
        )
        data = build_public_machine_load_product_model_service().annotate_public_queue(data)
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.get("/{token}/performance")
def get_public_machine_load_performance(
    token: str,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    work_center: str = Query(
        ...,
        alias="workCenter",
        description="Centro de trabalho do operador, obrigatoriamente na fila publicada",
    ),
    days: int | None = Query(
        default=None,
        description="Janela dos gráficos em dias (7 a 30, padrão 14)",
    ),
):
    """Eficiência do turno e paradas do posto — agregados, sem nomes e sem valores em R$."""
    try:
        data = build_public_work_center_performance_service().build(
            token=token,
            branch=branch,
            work_center=work_center,
            days=days,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.get("/{token}/performance/downtime-items")
def get_public_machine_load_downtime_items(
    token: str,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    work_center: str = Query(
        ...,
        alias="workCenter",
        description="Centro de trabalho do operador, obrigatoriamente na fila publicada",
    ),
):
    """Paradas de hoje no turno atual do posto — motivo e observação, sem R$."""
    try:
        data = build_public_work_center_downtime_items_service().list_for_work_center(
            token=token,
            branch=branch,
            work_center=work_center,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.get("/{token}/operations/appointments")
def get_public_machine_load_operation_appointments(
    token: str,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    production_order: str = Query(
        ...,
        alias="productionOrder",
        description="OP da fila publicada",
    ),
    operation_code: str = Query(
        ...,
        alias="operationCode",
        description="Código da operação na fila publicada",
    ),
):
    """Histórico de apontamentos da OP+operação — data, quantidade e nome do operador."""
    try:
        data = build_public_operation_appointments_service().list_for_operation(
            token=token,
            branch=branch,
            production_order=production_order,
            operation_code=operation_code,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.get("/{token}/operations/materials")
def get_public_machine_load_operation_materials(
    token: str,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    production_order: str = Query(
        ...,
        alias="productionOrder",
        description="OP da fila publicada",
    ),
    operation_code: str = Query(
        ...,
        alias="operationCode",
        description="Código da operação na fila publicada",
    ),
):
    """Materiais SD4 da OP+operação — código, descrição, UM, original, saldo e consumido."""
    try:
        data = build_public_operation_materials_service().list_for_operation(
            token=token,
            branch=branch,
            production_order=production_order,
            operation_code=operation_code,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.get("/{token}/operations/process-inspections")
def get_public_machine_load_operation_process_inspections(
    token: str,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    production_order: str = Query(
        ...,
        alias="productionOrder",
        description="OP da fila publicada",
    ),
    operation_code: str = Query(
        ...,
        alias="operationCode",
        description="Código da operação na fila publicada",
    ),
):
    """Inspeções de processo da OP+operação — quem, quando e resultado (sem ensaios)."""
    try:
        data = build_public_operation_process_inspections_service().list_for_operation(
            token=token,
            branch=branch,
            production_order=production_order,
            operation_code=operation_code,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.get("/{token}/drawings/{pa_code}/pdf")
def get_public_machine_load_drawing_pdf(
    token: str,
    pa_code: str,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
):
    """PDF do desenho do PA, somente se o código estiver na fila publicada da filial."""
    try:
        drawing = build_public_machine_load_drawing_service().open_pdf(
            token=token,
            branch=branch,
            pa_code=pa_code,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return drawing_pdf_response(drawing)


@router.get("/{token}/models/{product_code}/glb")
def get_public_machine_load_product_model_glb(
    token: str,
    product_code: str,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
):
    """GLB do produto da OP, somente se o código estiver na fila publicada da filial."""
    try:
        model = build_public_machine_load_product_model_service().open_glb(
            token=token,
            branch=branch,
            product_code=product_code,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return FileResponse(
        model.path,
        media_type=model.media_type or "model/gltf-binary",
        filename=model.filename,
        content_disposition_type="inline",
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/{token}/bench-sessions")
def create_bench_session(token: str, body: BenchSessionBody):
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    if not _honeypot_ok(body.website):
        return ok({"accepted": True, "sessionToken": None})
    try:
        build_branch_access_service().assert_valid_branch(body.branch)
        data = build_production_run_service().create_bench_session(
            branch=body.branch,
            work_center=body.work_center,
            operator_code=body.operator_code,
            operator_name=body.operator_name,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.delete("/{token}/bench-sessions/current")
def end_bench_session(
    token: str,
    session_token: str | None = Header(default=None, alias=_BENCH_SESSION_HEADER),
):
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    try:
        build_production_run_service().end_bench_session(session_token)
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok({"ended": True})


@router.post("/{token}/runs")
def start_production_run(
    token: str,
    body: StartRunBody,
    session_token: str | None = Header(default=None, alias=_BENCH_SESSION_HEADER),
):
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    if not _honeypot_ok(body.website):
        return ok({"accepted": True, "id": None})
    try:
        build_branch_access_service().assert_valid_branch(body.branch)
        data = build_production_run_service().start_run(
            branch=body.branch,
            work_center=body.work_center,
            production_order=body.production_order,
            operation_code=body.operation_code,
            session_token=session_token,
            planned_qty=body.planned_qty,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.post("/{token}/runs/{run_id}/pause")
def pause_production_run(
    token: str,
    run_id: str,
    session_token: str | None = Header(default=None, alias=_BENCH_SESSION_HEADER),
):
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    try:
        data = build_production_run_service().pause_run(run_id, session_token=session_token)
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.post("/{token}/runs/{run_id}/resume")
def resume_production_run(
    token: str,
    run_id: str,
    session_token: str | None = Header(default=None, alias=_BENCH_SESSION_HEADER),
):
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    try:
        data = build_production_run_service().resume_run(run_id, session_token=session_token)
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.post("/{token}/runs/{run_id}/stop")
def stop_production_run(
    token: str,
    run_id: str,
    session_token: str | None = Header(default=None, alias=_BENCH_SESSION_HEADER),
):
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    try:
        data = build_production_run_service().stop_run(run_id, session_token=session_token)
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.get("/{token}/runs/active")
def get_active_production_run(
    token: str,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    work_center: str = Query(..., alias="workCenter", description="Centro de trabalho"),
):
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    try:
        build_branch_access_service().assert_valid_branch(branch)
        service = build_production_run_service()
        data = service.get_active(branch=branch, work_center=work_center)
        if data is not None:
            produced_qty = None
            try:
                queue = build_machine_load_service().build_public(
                    branch=branch,
                    work_center=work_center,
                )
                for op in (queue or {}).get("operations") or []:
                    if not isinstance(op, dict):
                        continue
                    if str(op.get("production_order") or "") != str(
                        data.get("productionOrder") or ""
                    ):
                        continue
                    if str(op.get("operation_code") or "") != str(data.get("operationCode") or ""):
                        continue
                    raw = op.get("operation_produced_qty")
                    if raw is None:
                        raw = op.get("produced_qty")
                    produced_qty = float(raw) if raw is not None else None
                    break
            except Exception:  # noqa: BLE001
                produced_qty = None
            if produced_qty is not None:
                counted = int(data.get("countedPieces") or data.get("piecesTotal") or 0)
                data = {
                    **data,
                    "totvsProducedQty": produced_qty,
                    "divergencePieces": counted - produced_qty,
                }
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.websocket("/{token}/ws")
async def public_machine_load_ws(
    websocket: WebSocket,
    token: str,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
):
    """Avisa o cockpit quando o PCP reordena a fila ou atualiza a partir do TOTVS."""
    if not build_public_cockpit_access_service().is_valid_token(token):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    try:
        room = build_branch_access_service().assert_valid_branch(branch)
    except InvalidBranch as exc:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from exc
    await machine_load_realtime_hub.connect(websocket, room=room)
