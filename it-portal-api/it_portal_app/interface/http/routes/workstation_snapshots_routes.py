"""G2-S2: canal de ingestao S2S, desabilitado sem flag e binding por workstation."""
from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from it_portal_app.application.workstation_snapshot_service import (
    INGEST_SCOPE, WorkstationSnapshotService,
)
from it_portal_app.application.workstation_identity_service import device_client_id
from it_portal_app.application.workstation_ports import WorkstationRepository
from it_portal_app.core.responses import ok
from it_portal_app.domain.errors import (
    ConflictError, NotFoundError, ValidationError,
)
from it_portal_app.interface.http.authz import COMPUTERS_VIEW, authorize
from it_portal_app.interface.http.dependencies import (
    get_workstation_repository, get_workstation_snapshot_service,
)
from it_portal_app.interface.http.s2s_auth import (require_collector_identity, require_dynamic_workstation_identity)
from it_portal_app.interface.http.schemas import Envelope, ERROR_RESPONSES
from it_portal_app.config import settings
from it_portal_app.domain.workstation_snapshots import MAX_PAYLOAD_BYTES

router = APIRouter(tags=["Workstation Snapshots"], responses=ERROR_RESPONSES)


@router.post(
    "/collector/v1/workstations/{workstation_id}/snapshots",
    operation_id="ingest_it_workstation_snapshot",
    status_code=201,
    response_model=Envelope[dict],
    summary="Ingere snapshot de inventario Windows via identidade S2S exclusiva",
)
async def ingest_workstation_snapshot(
    request: Request,
    workstation_id: UUID,
    service: WorkstationSnapshotService = Depends(get_workstation_snapshot_service),
):
    # Nao aceitar credencial humana. A feature continua fechada se a flag estiver off.
    if not settings.WORKSTATION_INGEST_ENABLED:
        raise ConflictError("workstation_ingest_disabled", "Ingestao de computadores desabilitada.")
    if settings.WORKSTATION_DB_BINDINGS_ENABLED:
        identity = require_dynamic_workstation_identity(
            request, expected_client_id=device_client_id(str(workstation_id)),
        )
    else:
        identity = require_collector_identity(
            request, required_scopes=(INGEST_SCOPE,),
        )
    content_type = request.headers.get("content-type", "").split(";", 1)[0].lower().strip()
    if content_type != "application/json":
        raise ValidationError("snapshot_content_type_invalid", "Envie JSON em application/json.")
    size = 0
    chunks: list[bytes] = []
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_PAYLOAD_BYTES:
            raise ValidationError("snapshot_too_large", "Snapshot excedeu limite de tamanho.")
        chunks.append(chunk)
    try:
        raw = json.loads(b"".join(chunks).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValidationError("snapshot_invalid_json", "Corpo JSON invalido.") from None

    result = service.ingest(str(workstation_id), raw, client_id=identity.client_id)
    code = 200 if result["duplicate"] else 201
    return ok(result, "Inventario registrado.", code, operation_id="ingest_it_workstation_snapshot")


@router.get(
    "/workstations/{workstation_id}/snapshot",
    operation_id="get_it_workstation_latest_snapshot",
    response_model=Envelope[dict | None],
    summary="Consulta ultimo inventario observado; nao representa online em tempo real",
)
def get_workstation_latest_snapshot(
    request: Request,
    workstation_id: UUID,
    service: WorkstationSnapshotService = Depends(get_workstation_snapshot_service),
    workstations: WorkstationRepository = Depends(get_workstation_repository),
):
    authorize(request, COMPUTERS_VIEW)
    if workstations.get_workstation(str(workstation_id)) is None:
        raise NotFoundError("workstation_not_found", "Computador nao encontrado.")
    return ok(
        service.latest(str(workstation_id)),
        operation_id="get_it_workstation_latest_snapshot",
    )
