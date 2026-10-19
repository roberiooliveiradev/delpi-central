from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Header, Query, Request
from pydantic import BaseModel, Field

from production_control_app.application.services.machine_load_service import (
    strip_all_operations,
)
from production_control_app.composition.pc_composer import (
    build_machine_load_cockpit_status_service,
    build_machine_load_service,
    build_pcp_process_issue_service,
)
from production_control_app.core.responses import fail, ok
from production_control_app.domain.services.machine_load_optimization import (
    MachineLoadOptimizationCriteria,
)
from production_control_app.domain.errors import (
    BranchAccessDenied,
    DelpiGatewayError,
    InvalidBranch,
    MachineLoadOperationNotFound,
    MachineLoadSequenceConflict,
    RequestsGatewayRejected,
    RequestsGatewayUnauthorized,
    RequestsGatewayUnavailable,
    SequencingProfileInvalid,
    SnapshotNotFound,
)
from production_control_app.infrastructure.persistence.plugins_postgres_connection import (
    PluginsDatabaseConfigError,
    PluginsDatabaseConnectionError,
)
from production_control_app.interface.http.auth_http import resolve_user

router = APIRouter(tags=["Machine load"])


def _include_all_centers_query() -> Any:
    """Opt-in pela fila completa da filial (todos os centros) no mesmo payload.

    O PCP troca de centro de trabalho sem nova leitura; consumidores que só
    precisam do centro ativo continuam recebendo o payload enxuto.
    """
    return Query(
        default=False,
        alias="includeAllCenters",
        description="Inclui a fila completa da filial (todos os centros) no payload",
    )


def _scoped(data: dict[str, Any], include_all_centers: bool) -> dict[str, Any]:
    return data if include_all_centers else strip_all_operations(data)


class SequenceKeyBody(BaseModel):
    production_order: str = Field(..., min_length=1, max_length=30)
    operation_code: str = Field(..., min_length=1, max_length=10)


class SequenceReorderBody(BaseModel):
    ordered_keys: list[SequenceKeyBody] = Field(default_factory=list)
    # Ordem-base que o cliente tinha na tela. Ausente (None) = cliente legado
    # de antes do contrato de concorrência — rejeitado com 409 e mensagem de
    # recarga; divergente do estado vigente = conflito 409, sem write.
    expected_keys: list[SequenceKeyBody] | None = None


class OperationKeyBody(BaseModel):
    # Identidade canônica de uma operação no lote — OP + operação.
    production_order: str = Field(..., min_length=1, max_length=30)
    operation_code: str = Field(..., min_length=1, max_length=10)


class OperationRefBody(OperationKeyBody):
    # Identidade completa — centro + OP + operação (retirada/restauração).
    work_center: str = Field(..., min_length=1, max_length=20)


class TransferOperationsBody(BaseModel):
    source_work_center: str = Field(..., min_length=1, max_length=20)
    target_work_center: str = Field(..., min_length=1, max_length=20)
    operations: list[OperationKeyBody] = Field(..., min_length=1, max_length=200)
    # Ordem vigente do CT de origem que o analista viu — obrigatória: divergir
    # do estado dentro do lock é 409, nunca write.
    expected_keys: list[SequenceKeyBody] = Field(..., min_length=1)


class WithdrawOperationsBody(BaseModel):
    operations: list[OperationRefBody] = Field(..., min_length=1, max_length=200)
    expected_keys: list[SequenceKeyBody] = Field(..., min_length=1)


class RestoreOperationsBody(BaseModel):
    operations: list[OperationRefBody] = Field(..., min_length=1, max_length=200)


class MachineLoadOptimizeCriteriaBody(BaseModel):
    """Critérios secundários da otimização — a data de entrega é sempre ativa."""
    group_by_tool: bool = False


class MachineLoadOptimizeBody(BaseModel):
    criteria: MachineLoadOptimizeCriteriaBody = Field(
        default_factory=MachineLoadOptimizeCriteriaBody
    )


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
    if isinstance(exc, (SnapshotNotFound, MachineLoadOperationNotFound)):
        return fail(str(exc), 404)
    if isinstance(exc, MachineLoadSequenceConflict):
        return fail(str(exc), 409)
    if isinstance(exc, RequestsGatewayUnauthorized):
        return fail(str(exc), 403)
    if isinstance(exc, RequestsGatewayRejected):
        return fail(str(exc), 422)
    if isinstance(exc, RequestsGatewayUnavailable):
        return fail(str(exc), 502)
    if isinstance(exc, SequencingProfileInvalid):
        return fail(str(exc), 422)
    if isinstance(exc, ValueError):
        return fail(str(exc), 422)
    if isinstance(exc, DelpiGatewayError):
        return fail(str(exc), 502)
    if isinstance(exc, (PluginsDatabaseConfigError, PluginsDatabaseConnectionError)):
        return fail("Estados de execução temporariamente indisponíveis.", 503)
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
    include_all_centers: bool = _include_all_centers_query(),
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
    return ok(_scoped(data, include_all_centers))


@router.get(
    "/machine-load/work-centers",
    operation_id="get_machine_load_work_centers",
)
def get_machine_load_work_centers(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
):
    """CTs da filial vindos do snapshot congelado — leitura administrativa sem
    efeitos colaterais: ausência de fila responde vazio, nunca puxa o TOTVS."""
    user = resolve_user(request)
    try:
        data = build_machine_load_service().stored_work_centers(
            user, branch=branch
        )
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(data)


@router.get("/machine-load/live-status")
def get_machine_load_live_status(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
):
    """Status de apontamento vivo (HZA) da fila: só as operações com apontamento.

    O MFE aplica estes campos sobre a fila congelada que já está na tela, sem
    recarregar a fila.
    """
    user = resolve_user(request)
    try:
        data = build_machine_load_service().live_status(user, branch=branch)
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(data)


@router.get(
    "/machine-load/cockpit-status",
    operation_id="get_machine_load_cockpit_status",
)
def get_machine_load_cockpit_status(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
):
    """Estados de execução registrados pelo cockpit (runs MES locais).

    Fonte oficial nova da execução — snapshot completo dos runs abertos da
    filial lido do PostgreSQL local, sem HZA/TOTVS nem Production Pulse.
    """
    user = resolve_user(request)
    try:
        data = build_machine_load_cockpit_status_service().cockpit_status(
            user, branch=branch
        )
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(data)


@router.get(
    "/machine-load/balances",
    operation_id="get_machine_load_balances",
)
def get_machine_load_balances(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
):
    """Saldos SH6/SC2 das operações da fila congelada — sem HZA.

    Quantidades produzidas e pendentes por operação, limitadas às OPs da
    programação visível. Execução é lida em ``/machine-load/cockpit-status``;
    este endpoint nunca consulta apontamentos HZA.
    """
    user = resolve_user(request)
    try:
        data = build_machine_load_service().operation_balances(user, branch=branch)
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
    include_all_centers: bool = _include_all_centers_query(),
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
    return ok(
        _scoped(data, include_all_centers),
        message="Carga máquina atualizada com os dados do TOTVS.",
    )


@router.post("/machine-load/publish")
def publish_machine_load(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
):
    """«Enviar para máquinas»: publica a fila WORKING vigente no cockpit.

    A fila sai sempre do snapshot persistido no backend — o corpo da
    requisição não é autoridade da publicação.
    """
    user = resolve_user(request)
    try:
        data = build_machine_load_service().publish(user, branch=branch)
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    changed = bool((data.get("publication") or {}).get("changed"))
    return ok(
        data,
        message=(
            "Carga máquina enviada para as máquinas."
            if changed
            else "A carga máquina atual já está enviada para as máquinas."
        ),
    )


@router.patch("/machine-load/sequence")
def patch_machine_load_sequence(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    work_center: str = Query(
        ...,
        alias="workCenter",
        description="Centro de trabalho cuja sequência será reordenada",
    ),
    include_all_centers: bool = _include_all_centers_query(),
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
            expected_keys=(
                [item.model_dump() for item in body.expected_keys]
                if body.expected_keys is not None
                else None
            ),
        )
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(_scoped(data, include_all_centers), message="Sequência da carga máquina salva.")


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
    include_all_centers: bool = _include_all_centers_query(),
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
    return ok(
        _scoped(data, include_all_centers),
        message=data.get("prioritization", {}).get("message"),
    )


@router.post("/machine-load/optimize-delivery")
def optimize_machine_load_delivery_sequence(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    work_center: str | None = Query(
        default=None,
        alias="workCenter",
        description="Centro de trabalho que continua ativo na resposta",
    ),
    include_all_centers: bool = _include_all_centers_query(),
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
    return ok(
        _scoped(data, include_all_centers),
        message=data.get("optimization", {}).get("message"),
    )


@router.post("/machine-load/optimize")
def optimize_machine_load_queue(
    request: Request,
    body: MachineLoadOptimizeBody | None = None,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    work_center: str | None = Query(
        default=None,
        alias="workCenter",
        description="Centro de trabalho que continua ativo na resposta",
    ),
    include_all_centers: bool = _include_all_centers_query(),
):
    """Otimização genérica: entrega do PA sempre ativa; critérios extras no body."""
    user = resolve_user(request)
    group_by_tool = body.criteria.group_by_tool if body else False
    try:
        data = build_machine_load_service().optimize_sequence(
            user,
            branch=branch,
            criteria=MachineLoadOptimizationCriteria(group_by_tool=group_by_tool),
            work_center=work_center,
        )
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(
        _scoped(data, include_all_centers),
        message=data.get("optimization", {}).get("message"),
    )


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
    include_all_centers: bool = _include_all_centers_query(),
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
    return ok(
        _scoped(data, include_all_centers),
        message=data.get("withdrawal", {}).get("message"),
    )


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
    include_all_centers: bool = _include_all_centers_query(),
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
    return ok(
        _scoped(data, include_all_centers),
        message=data.get("withdrawal", {}).get("message"),
    )


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
    include_all_centers: bool = _include_all_centers_query(),
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
    return ok(
        _scoped(data, include_all_centers),
        message=data.get("transfer", {}).get("message"),
    )


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
    include_all_centers: bool = _include_all_centers_query(),
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
    return ok(
        _scoped(data, include_all_centers),
        message=data.get("transfer", {}).get("message"),
    )


@router.post("/machine-load/transfer-operations")
def transfer_machine_load_operations(
    request: Request,
    body: TransferOperationsBody = Body(...),
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    work_center: str | None = Query(
        default=None,
        alias="workCenter",
        description="Centro de trabalho que continua ativo na resposta; vazio usa a origem",
    ),
    include_all_centers: bool = _include_all_centers_query(),
):
    """Move as operações selecionadas do centro de origem para o fim da fila do destino."""
    user = resolve_user(request)
    try:
        data = build_machine_load_service().transfer_operations(
            user,
            branch=branch,
            source_work_center=body.source_work_center,
            target_work_center=body.target_work_center,
            operations=[item.model_dump() for item in body.operations],
            expected_keys=[item.model_dump() for item in body.expected_keys],
            work_center=work_center,
        )
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(
        _scoped(data, include_all_centers),
        message=data.get("transfer", {}).get("message"),
    )


@router.post("/machine-load/withdraw-operations")
def withdraw_machine_load_operations(
    request: Request,
    body: WithdrawOperationsBody = Body(...),
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    work_center: str | None = Query(
        default=None,
        alias="workCenter",
        description="Centro de trabalho que continua ativo na resposta",
    ),
    include_all_centers: bool = _include_all_centers_query(),
):
    """Retira da programação somente as operações selecionadas (não é o conjunto)."""
    user = resolve_user(request)
    try:
        data = build_machine_load_service().withdraw_operations(
            user,
            branch=branch,
            operations=[item.model_dump() for item in body.operations],
            expected_keys=[item.model_dump() for item in body.expected_keys],
            work_center=work_center,
        )
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(
        _scoped(data, include_all_centers),
        message=data.get("withdrawal", {}).get("message"),
    )


@router.post("/machine-load/restore-operations")
def restore_machine_load_operations(
    request: Request,
    body: RestoreOperationsBody = Body(...),
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    work_center: str | None = Query(
        default=None,
        alias="workCenter",
        description="Centro de trabalho que continua ativo na resposta",
    ),
    include_all_centers: bool = _include_all_centers_query(),
):
    """Devolve à fila operações retiradas individualmente — não restaura o conjunto."""
    user = resolve_user(request)
    try:
        data = build_machine_load_service().restore_operations(
            user,
            branch=branch,
            operations=[item.model_dump() for item in body.operations],
            work_center=work_center,
        )
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(
        _scoped(data, include_all_centers),
        message=data.get("withdrawal", {}).get("message"),
    )


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


class ReportProcessIssueBody(BaseModel):
    """Solicitação de correção a Processos aberta pela Carga Máquina (PCP).

    A identidade do analista nunca vem do payload — é resolvida do JWT no
    backend. Filial e CT são revalidados contra a fila WORKING vigente.
    """

    work_center: str = Field(..., min_length=1, max_length=20)
    production_order: str = Field(..., min_length=1, max_length=30)
    operation_code: str = Field(..., min_length=1, max_length=10)
    issue_code: str = Field(..., min_length=1, max_length=60)
    tool_code: str | None = Field(default=None, max_length=60)
    material_code: str | None = Field(default=None, max_length=60)
    note: str | None = Field(default=None, max_length=500)


@router.post(
    "/machine-load/process-issues",
    operation_id="create_machine_load_process_issue",
)
def create_machine_load_process_issue(
    request: Request,
    body: ReportProcessIssueBody = Body(...),
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        description="Chave da tentativa lógica — deduplica retries/dup clique",
    ),
):
    """Abre uma solicitação process-issue em nome do analista autenticado.

    Somente registra o chamado no fluxo existente de Processos — não altera
    sequenciamento, execução nem dados do TOTVS.
    """
    user = resolve_user(request)
    try:
        data = build_pcp_process_issue_service().report(
            user,
            branch=branch,
            work_center=body.work_center,
            production_order=body.production_order,
            operation_code=body.operation_code,
            issue_code=body.issue_code,
            tool_code=body.tool_code,
            material_code=body.material_code,
            note=body.note,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _handle_machine_load_errors(exc)
    return ok(data, message=data.get("message") or "OK", status_code=201)
