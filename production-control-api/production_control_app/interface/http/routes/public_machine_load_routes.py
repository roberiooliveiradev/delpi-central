"""Cockpit público do operador — leitura anônima da fila e aviso de mudança em tempo real."""

from __future__ import annotations

from fastapi import (
    APIRouter,
    Header,
    Query,
    WebSocket,
    WebSocketException,
    status,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from production_control_app.application.services.machine_load_realtime_hub import (
    machine_load_realtime_hub,
)
from production_control_app.composition.pc_composer import (
    build_branch_access_service,
    build_machine_load_service,
    build_mes_downtime_classification_service,
    build_mes_run_timeline_service,
    build_production_run_service,
    build_public_cockpit_access_service,
    build_public_machine_load_drawing_service,
    build_public_machine_load_product_model_service,
    build_public_operation_appointments_service,
    build_public_operation_materials_service,
    build_public_operation_process_inspections_service,
    build_public_work_center_downtime_items_service,
    build_public_work_center_downtime_source_service,
    build_public_mes_work_center_period_service,
    build_public_mes_work_center_today_service,
    build_public_work_center_performance_service,
)
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import (
    BenchSessionRequired,
    DelpiGatewayError,
    DowntimeConflict,
    DowntimeSourceUnavailable,
    DowntimeNotFound,
    DrawingNotFound,
    DrawingSourceUnavailable,
    InvalidBranch,
    InvalidMesEvent,
    MesStateConflict,
    InvalidOperatorRegistration,
    OperatorDirectoryContractError,
    OperatorDirectoryUnavailable,
    InvalidOperatorFeedbackMaterials,
    InvalidOperatorFeedbackReason,
    InvalidOperatorFeedbackType,
    OperatorFeedbackConflict,
    OperatorFeedbackNotFound,
    OperatorFeedbackStateError,
    OperatorInactive,
    OperatorNotFound,
    Product3DModelNotFound,
    ProductionRunConflict,
    ProductionRunHandoffConflict,
    ProductionRunNotFound,
    PublicAccessDenied,
    PulseDeviceUnavailable,
    PulseGatewayError,
    RequestsGatewayRejected,
    RequestsGatewayUnavailable,
    SnapshotNotFound,
)
from production_control_app.interface.http.drawing_response import drawing_pdf_response

router = APIRouter(prefix="/public/machine-load", tags=["Public machine load"])

_BENCH_SESSION_HEADER = "X-Delpi-Bench-Session"


class BenchSessionBody(BaseModel):
    model_config = {"populate_by_name": True}

    branch: str = Field(..., min_length=2, max_length=2)
    work_center: str = Field(..., alias="workCenter", min_length=1, max_length=40)
    registration: str | None = Field(
        default=None,
        max_length=40,
        description="Matrícula oficial do colaborador (Portal RH) — campo canônico.",
    )
    # DEPRECATED (C3→C4): alias legado da matrícula, usado até o cockpit ser
    # redesenhado. Se registration + operatorCode divergirem → 422.
    operator_code: str | None = Field(
        default=None,
        alias="operatorCode",
        max_length=40,
        description="DEPRECATED: alias legado temporário de registration.",
    )
    # DEPRECATED: ignorado como fonte de identidade — o nome vem do Portal RH.
    operator_name: str | None = Field(
        default=None,
        alias="operatorName",
        max_length=120,
        description="DEPRECATED: ignorado; o nome oficial é resolvido no Portal RH.",
    )
    website: str | None = None  # honeypot


class ClassifyDowntimeBody(BaseModel):
    model_config = {"populate_by_name": True}

    reason_code: str = Field(..., alias="reasonCode", min_length=1, max_length=40)
    note: str | None = Field(default=None, max_length=500)
    website: str | None = None  # honeypot


class StartRunBody(BaseModel):
    model_config = {"populate_by_name": True}

    branch: str = Field(..., min_length=2, max_length=2)
    work_center: str = Field(..., alias="workCenter", min_length=1, max_length=40)
    production_order: str = Field(..., alias="productionOrder", min_length=1, max_length=40)
    operation_code: str = Field(..., alias="operationCode", min_length=1, max_length=20)
    planned_qty: float | None = Field(
        default=None,
        alias="plannedQty",
        deprecated=True,
        description="Legado ignorado; a meta vem da operação localizada no backend.",
    )
    website: str | None = None  # honeypot


class HandoffExpectedNextBody(BaseModel):
    model_config = {"populate_by_name": True}

    production_order: str = Field(
        ..., alias="productionOrder", min_length=1, max_length=40
    )
    operation_code: str = Field(
        ..., alias="operationCode", min_length=1, max_length=20
    )


class RunHandoffBody(BaseModel):
    model_config = {"populate_by_name": True}

    request_id: str = Field(
        ...,
        alias="requestId",
        min_length=1,
        max_length=64,
        description="UUID gerado uma vez por confirmação (idempotência).",
    )
    branch: str = Field(..., min_length=2, max_length=2)
    work_center: str = Field(..., alias="workCenter", min_length=1, max_length=40)
    expected_next: HandoffExpectedNextBody = Field(..., alias="expectedNext")
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
    if isinstance(exc, ProductionRunHandoffConflict):
        return fail(str(exc), 409, data={"code": exc.code})
    if isinstance(exc, ProductionRunConflict):
        return fail(str(exc), 409)
    if isinstance(exc, ProductionRunNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, (MesStateConflict, DowntimeConflict)):
        return fail(str(exc), 409)
    if isinstance(exc, DowntimeNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, InvalidMesEvent):
        return fail(str(exc), 422)
    if isinstance(exc, PulseDeviceUnavailable):
        return fail(str(exc), 422)
    if isinstance(exc, DowntimeSourceUnavailable):
        return fail(str(exc), 503)
    if isinstance(exc, PulseGatewayError):
        return fail(str(exc), 502)
    if isinstance(
        exc,
        (
            InvalidOperatorFeedbackType,
            InvalidOperatorFeedbackReason,
            InvalidOperatorFeedbackMaterials,
        ),
    ):
        return fail(str(exc), 422)
    if isinstance(exc, OperatorFeedbackConflict):
        return fail("O PCP já foi informado sobre este impedimento.", 409)
    if isinstance(exc, OperatorFeedbackNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, OperatorFeedbackStateError):
        return fail(str(exc), 409)
    if isinstance(exc, InvalidOperatorRegistration):
        return fail(str(exc), 422)
    if isinstance(exc, OperatorNotFound):
        return fail("Matrícula não encontrada.", 404)
    if isinstance(exc, OperatorInactive):
        return fail(str(exc), 403)
    # Diretório indisponível/credencial S2S/contrato upstream → 503 genérico;
    # detalhes ficam só nos logs técnicos (nunca token/URL para o browser).
    if isinstance(exc, (OperatorDirectoryUnavailable, OperatorDirectoryContractError)):
        return fail("Não foi possível validar a matrícula no momento.", 503)
    # P2 — Requests API: rejeição 4xx propaga a mensagem PT do domínio;
    # indisponibilidade/credencial → 503 amigável (nunca sucesso falso).
    if isinstance(exc, RequestsGatewayRejected):
        return fail(str(exc), 422)
    if isinstance(exc, RequestsGatewayUnavailable):
        return fail(
            "Não foi possível enviar a solicitação para Processos. "
            "Tente novamente.",
            503,
        )
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
    registration = (body.registration or "").strip()
    legacy = (body.operator_code or "").strip()
    if registration and legacy and registration != legacy:
        return fail("Matrícula divergente entre 'registration' e 'operatorCode'.", 422)
    effective = registration or legacy
    if not effective:
        return fail("Informe a matrícula do operador.", 422)
    try:
        build_branch_access_service().assert_valid_branch(body.branch)
        data = build_production_run_service().create_bench_session(
            branch=body.branch,
            work_center=body.work_center,
            registration=effective,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.get("/{token}/bench-sessions/current")
def get_current_bench_session(
    token: str,
    session_token: str | None = Header(default=None, alias=_BENCH_SESSION_HEADER),
):
    """Restore do cockpit: devolve a sessão persistida (sem consultar o RH)."""
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    try:
        data = build_production_run_service().get_current_bench_session(session_token)
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


@router.get(
    "/{token}/runs/{run_id}/handoff-preview",
    operation_id="get_public_run_handoff_preview",
)
def get_run_handoff_preview(
    token: str,
    run_id: str,
    branch: str = Query(...),
    work_center: str = Query(..., alias="workCenter"),
    session_token: str | None = Header(default=None, alias=_BENCH_SESSION_HEADER),
):
    """Prévia da troca guiada: run atual + próxima elegível da PUBLISHED.

    Leitura pura — não muda run, contagem nem fila. A decisão de qual
    operação sucede é do backend (filial + CT + ordem publicada); o cockpit
    apenas apresenta.
    """
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    try:
        data = build_production_run_service().handoff_preview(
            run_id,
            session_token=session_token,
            branch=branch,
            work_center=work_center,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.post(
    "/{token}/runs/{run_id}/handoff",
    operation_id="confirm_public_run_handoff",
)
def confirm_run_handoff(
    token: str,
    run_id: str,
    body: RunHandoffBody,
    session_token: str | None = Header(default=None, alias=_BENCH_SESSION_HEADER),
):
    """Confirmação atômica da troca: encerra o run e inicia o sucessor.

    O backend recalcula o destino sobre a PUBLISHED travada e confere com
    expectedNext — a prévia nunca é autorização. requestId torna a
    operação idempotente: replay devolve o resultado original gravado.
    """
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    if not _honeypot_ok(body.website):
        return ok({"accepted": True, "id": None})
    try:
        build_branch_access_service().assert_valid_branch(body.branch)
        data = build_production_run_service().confirm_handoff(
            run_id,
            request_id=body.request_id,
            branch=body.branch,
            work_center=body.work_center,
            expected_next={
                "productionOrder": body.expected_next.production_order,
                "operationCode": body.expected_next.operation_code,
            },
            session_token=session_token,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.get(
    "/{token}/downtime-source",
    operation_id="get_public_work_center_downtime_source",
)
def get_public_work_center_downtime_source(
    token: str,
    branch: str = Query(..., min_length=2, max_length=2),
    work_center: str = Query(..., alias="workCenter", max_length=40),
):
    """Fonte de paradas do posto no cockpit: mes, totvs ou unavailable.

    Somente leitura — nunca consulta TOTVS, nunca escreve. unavailable
    é resposta válida de resolução, sem fallback automático para TOTVS.
    """
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    try:
        data = build_public_work_center_downtime_source_service().resolve(
            token=token,
            branch=branch,
            work_center=work_center,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.get(
    "/{token}/mes/work-centers",
    summary="Listar centros de trabalho sensorizados",
    description=(
        "CTs com vínculo pulse_counter ativo na filial — inclui postos "
        "sem operação publicada (monitoramento autônomo). Token obrigatório; "
        "detalhes operacionais exigem sessão de bancada do posto."
    ),
    operation_id="public_mes_work_centers_sensorized",
    tags=["Public - Machine Load"],
)
def public_mes_work_centers_sensorized(
    token: str,
    branch: str = Query(..., min_length=2, max_length=2),
):
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    try:
        data = build_public_work_center_downtime_source_service().list_sensorized(
            token=token, branch=branch
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.get(
    "/{token}/mes/work-centers/today",
    operation_id="get_public_mes_work_center_today",
)
def get_public_mes_work_center_today(
    token: str,
    branch: str = Query(..., min_length=2, max_length=2),
    work_center: str = Query(..., alias="workCenter", max_length=40),
    session_token: str | None = Header(default=None, alias=_BENCH_SESSION_HEADER),
):
    """Linha do tempo MES do posto no dia civil — sessão de bancada
    obrigatória; leitura sem efeitos."""
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    try:
        data = build_public_mes_work_center_today_service().get_today(
            token=token,
            branch=branch,
            work_center=work_center,
            session_token=session_token,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.get(
    "/{token}/mes/work-centers/period",
    operation_id="get_public_mes_work_center_period",
)
def get_public_mes_work_center_period(
    token: str,
    branch: str = Query(..., min_length=2, max_length=2),
    work_center: str = Query(..., alias="workCenter", max_length=40),
    days: int = Query(default=7, ge=1, le=31),
    session_token: str | None = Header(default=None, alias=_BENCH_SESSION_HEADER),
):
    """Resumo MES do posto por período de dias civis — sessão de bancada
    obrigatória; alimenta o painel de desempenho de CTs sensorizados."""
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    try:
        data = build_public_mes_work_center_period_service().get_period(
            token=token,
            branch=branch,
            work_center=work_center,
            session_token=session_token,
            days=days,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.get("/{token}/mes/downtime-reasons")
def get_mes_downtime_reasons(token: str):
    """Catálogo MES de motivos de parada ativos (não confundir com paradas TOTVS)."""
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    try:
        items = build_mes_downtime_classification_service().list_reasons()
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok({"items": items})


@router.get("/{token}/mes/downtimes/pending")
def list_pending_mes_downtimes(
    token: str,
    branch: str = Query(..., min_length=2, max_length=2),
    work_center: str = Query(..., alias="workCenter", max_length=40),
    session_token: str | None = Header(default=None, alias=_BENCH_SESSION_HEADER),
):
    """Paradas MES encerradas do posto ainda sem motivo — sessão de bancada
    obrigatória; inclui paradas de runs já encerrados."""
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    try:
        items = build_mes_downtime_classification_service().list_unclassified(
            branch=branch,
            work_center=work_center,
            session_token=session_token,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok({"items": items})


@router.post("/{token}/runs/{run_id}/downtime/classify")
def classify_run_downtime(
    token: str,
    run_id: str,
    body: ClassifyDowntimeBody,
    session_token: str | None = Header(default=None, alias=_BENCH_SESSION_HEADER),
):
    """Confirma ou altera o motivo da parada aberta do run (nunca cria outra)."""
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    if not _honeypot_ok(body.website):
        return ok({"accepted": True, "id": None})
    try:
        data = build_mes_downtime_classification_service().classify(
            run_id,
            reason_code=body.reason_code,
            note=body.note,
            session_token=session_token,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.post("/{token}/runs/{run_id}/downtimes/{downtime_id}/classify")
def classify_run_downtime_by_id(
    token: str,
    run_id: str,
    downtime_id: str,
    body: ClassifyDowntimeBody,
    session_token: str | None = Header(default=None, alias=_BENCH_SESSION_HEADER),
):
    """Classifica uma parada específica do run (inclui parada automática já
    encerrada sem motivo). O downtime deve pertencer ao run informado."""
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    if not _honeypot_ok(body.website):
        return ok({"accepted": True, "id": None})
    try:
        data = build_mes_downtime_classification_service().classify(
            run_id,
            reason_code=body.reason_code,
            note=body.note,
            session_token=session_token,
            downtime_id=downtime_id,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.post(
    "/{token}/mes/downtimes/{downtime_id}/classify",
    operation_id="classify_public_mes_work_center_downtime",
)
def classify_work_center_downtime(
    token: str,
    downtime_id: str,
    body: ClassifyDowntimeBody,
    session_token: str | None = Header(default=None, alias=_BENCH_SESSION_HEADER),
):
    """Classifica a parada pela identidade real + escopo do CT da sessão.

    PC-MES-CT-AUTONOMOUS-DOWNTIME (RQ-07): cobre paradas sem run
    (monitoramento autônomo) e qualquer parada do posto — aberta ou
    encerrada. O endpoint legado por run permanece o contrato para quem
    conhece o runId.
    """
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    if not _honeypot_ok(body.website):
        return ok({"accepted": True, "id": None})
    try:
        data = build_mes_downtime_classification_service().classify_work_center_downtime(
            downtime_id,
            reason_code=body.reason_code,
            note=body.note,
            session_token=session_token,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.get("/{token}/runs/{run_id}/timeline")
def get_run_timeline(
    token: str,
    run_id: str,
    session_token: str | None = Header(default=None, alias=_BENCH_SESSION_HEADER),
):
    """Timeline operacional do run (estados + paradas derivadas)."""
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    try:
        data = build_mes_run_timeline_service().get_timeline(
            run_id, session_token=session_token
        )
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
            pieces_factor = None
            try:
                qty = build_machine_load_service().public_operation_run_quantity(
                    branch=branch,
                    work_center=work_center,
                    production_order=str(data.get("productionOrder") or ""),
                    operation_code=str(data.get("operationCode") or ""),
                )
                if qty is not None:
                    produced_qty = qty.get("operation_produced_qty")
                    pieces_factor = qty.get("pieces_conversion_factor")
            except Exception:  # noqa: BLE001
                produced_qty = None
            if produced_qty is not None:
                counted = int(data.get("countedPieces") or data.get("piecesTotal") or 0)
                counted_operator = (
                    counted / pieces_factor
                    if isinstance(pieces_factor, (int, float)) and pieces_factor > 0
                    else counted
                )
                data = {
                    **data,
                    "totvsProducedQty": produced_qty,
                    "divergencePieces": counted_operator - produced_qty,
                    "piecesConversionFactor": pieces_factor,
                }
            elif pieces_factor is not None:
                data = {**data, "piecesConversionFactor": pieces_factor}
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
