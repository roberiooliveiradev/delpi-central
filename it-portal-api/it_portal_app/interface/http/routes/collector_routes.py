"""Ingestão S2S de observações do coletor Linux (E4.S1)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request

from it_portal_app.application.observation_service import ObservationService
from it_portal_app.core.responses import ok
from it_portal_app.interface.http.dependencies import get_observation_service
from it_portal_app.interface.http.s2s_auth import (
    OBSERVATIONS_INGEST_SCOPE,
    require_collector_identity,
)
from it_portal_app.interface.http.schemas import (
    ERROR_RESPONSES,
    Envelope,
    ObservationIngestInput,
    ObservationOut,
)

router = APIRouter(prefix="/collector/v1", tags=["Collector"], responses=ERROR_RESPONSES)


@router.post(
    "/servers/{server_id}/observations",
    operation_id="ingest_it_server_observation",
    response_model=Envelope[ObservationOut],
    status_code=201,
    summary="Ingere observação automática de um servidor (S2S)",
)
def ingest_it_server_observation(
    request: Request,
    server_id: UUID,
    body: ObservationIngestInput,
    service: ObservationService = Depends(get_observation_service),
):
    identity = require_collector_identity(
        request,
        required_scopes=(OBSERVATIONS_INGEST_SCOPE,),
    )
    saved = service.ingest(
        str(server_id),
        body.model_dump(),
        collector_client_id=identity.client_id,
    )
    return ok(saved, message="Observação registrada.", status_code=201, operation_id="ingest_it_server_observation")
