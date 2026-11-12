"""Windows SCM inventory: S2S ingestion and human read-only listing."""
from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from it_portal_app.application.host_service_inventory import HostServiceInventory
from it_portal_app.core.responses import ok
from it_portal_app.domain.host_services import VALID_STATES, VALID_START_MODES
from it_portal_app.domain.errors import ValidationError
from it_portal_app.interface.http.authz import SERVERS_VIEW, authorize
from it_portal_app.interface.http.dependencies import get_host_service_inventory
from it_portal_app.interface.http.s2s_auth import require_collector_identity
from it_portal_app.interface.http.schemas import Envelope, ERROR_RESPONSES, HostServiceBatchInput, HostServiceBatchReceipt, HostServicePage

router = APIRouter(tags=["Windows Host Services"], responses=ERROR_RESPONSES)
INGEST_SCOPE = "it-portal.host-services.ingest"

@router.post("/collector/v1/servers/{server_id}/host-services/batches",
    operation_id="ingest_it_windows_host_service_batch",
    response_model=Envelope[HostServiceBatchReceipt], status_code=201)
def ingest_batch(request: Request, server_id: UUID, body: HostServiceBatchInput,
    service: HostServiceInventory = Depends(get_host_service_inventory)):
    identity = require_collector_identity(request, required_scopes=(INGEST_SCOPE,))
    result = service.ingest(str(server_id), body.model_dump(), collector_client_id=identity.client_id)
    return ok(result, "Lote recebido.", 201, operation_id="ingest_it_windows_host_service_batch")

@router.get("/servers/{server_id}/host-services",
    operation_id="list_it_windows_host_services", response_model=Envelope[HostServicePage])
def list_host_services(request: Request, server_id: UUID,
    q: str | None = Query(default=None, max_length=120),
    state: str | None = Query(default=None),
    start_mode: str | None = Query(default=None),
    present: Literal["yes","no","all"] = Query(default="yes"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    service: HostServiceInventory = Depends(get_host_service_inventory)):
    authorize(request, SERVERS_VIEW)
    if state is not None and state not in VALID_STATES:
        raise ValidationError("invalid_state", "Filtro de estado inválido.")
    if start_mode is not None and start_mode not in VALID_START_MODES:
        raise ValidationError("invalid_start_mode", "Filtro de inicialização inválido.")
    data = service.list_services(str(server_id), q=q, state=state, start_mode=start_mode,
        present=present, page=page, page_size=page_size)
    return ok(data, operation_id="list_it_windows_host_services")
