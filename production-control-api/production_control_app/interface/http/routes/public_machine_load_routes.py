"""Cockpit público do operador — leitura anônima da fila e aviso de mudança em tempo real."""

from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketException, status
from fastapi.responses import FileResponse

from production_control_app.application.services.machine_load_realtime_hub import (
    machine_load_realtime_hub,
)
from production_control_app.composition.pc_composer import (
    build_branch_access_service,
    build_machine_load_service,
    build_public_cockpit_access_service,
    build_public_machine_load_drawing_service,
    build_public_machine_load_product_model_service,
    build_public_operation_appointments_service,
    build_public_work_center_downtime_items_service,
    build_public_work_center_performance_service,
)
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import (
    DelpiGatewayError,
    DrawingNotFound,
    InvalidBranch,
    Product3DModelNotFound,
    PublicAccessDenied,
    SnapshotNotFound,
)

router = APIRouter(prefix="/public/machine-load", tags=["Public machine load"])


def _handle_public_errors(exc: Exception):
    if isinstance(exc, PublicAccessDenied):
        return fail(str(exc), 404)
    if isinstance(exc, InvalidBranch):
        return fail(str(exc), 422)
    if isinstance(exc, SnapshotNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, DrawingNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, Product3DModelNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, ValueError):
        return fail(str(exc), 422)
    if isinstance(exc, DelpiGatewayError):
        return fail(str(exc), 502)
    raise exc


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
    return FileResponse(
        drawing.path,
        media_type=drawing.media_type or "application/pdf",
        filename=drawing.filename,
        content_disposition_type="inline",
        headers={"Cache-Control": "no-store"},
    )


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
