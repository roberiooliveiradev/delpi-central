"""#1585: comandos humanos e relay S2S restrito ao agente autorizado."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request

from it_portal_app.application.host_service_control import HostServiceControl
from it_portal_app.core.responses import ok
from it_portal_app.interface.http.authz import (
    SERVERS_VIEW, HOST_SERVICES_CONTROL, actor_from, authorize, authorize_write,
)
from it_portal_app.interface.http.dependencies import get_host_service_control
from it_portal_app.interface.http.s2s_auth import require_collector_identity
from it_portal_app.interface.http.schemas import (
    Envelope, ERROR_RESPONSES, HostServiceActionInput, HostServiceActionOut,
    HostServiceAgentPollInput,
    HostServiceAgentClaimOut, HostServiceAgentReportInput,
)

router = APIRouter(tags=["Windows Host Service Actions"], responses=ERROR_RESPONSES)
AGENT_SCOPE = "it-portal.host-services.control-agent"


@router.post("/servers/{server_id}/host-services/{service_name}/actions",
    operation_id="request_it_windows_host_service_action",
    response_model=Envelope[HostServiceActionOut], status_code=202)
def request_action(request: Request, server_id: UUID, service_name: str,
                   body: HostServiceActionInput,
                   service: HostServiceControl = Depends(get_host_service_control)):
    # Fresh effective RBAC no Core, separado de favoritos e da coleta.
    actor = actor_from(authorize_write(request, SERVERS_VIEW, HOST_SERVICES_CONTROL))
    result = service.submit(
        str(server_id), service_name, body.action, str(body.request_id),
        confirmed=body.confirmed, actor=actor,
    )
    return ok(result, "Solicitação enviada ao servidor.", 202,
              operation_id="request_it_windows_host_service_action")


@router.get("/servers/{server_id}/host-services/actions/{action_id}",
    operation_id="get_it_windows_host_service_action",
    response_model=Envelope[HostServiceActionOut])
def get_action(request: Request, server_id: UUID, action_id: UUID,
               service: HostServiceControl = Depends(get_host_service_control)):
    authorize(request, SERVERS_VIEW, HOST_SERVICES_CONTROL)
    return ok(service.status(str(server_id), str(action_id)),
              operation_id="get_it_windows_host_service_action")


@router.post("/collector/v1/servers/{server_id}/host-services/control/next",
    operation_id="claim_it_windows_host_service_action",
    response_model=Envelope[HostServiceAgentClaimOut | None])
def claim_action(request: Request, server_id: UUID, body: HostServiceAgentPollInput,
                 service: HostServiceControl = Depends(get_host_service_control)):
    identity = require_collector_identity(request, required_scopes=(AGENT_SCOPE,))
    result = service.poll(str(server_id), identity.client_id, body.hostname)
    return ok(result, operation_id="claim_it_windows_host_service_action")


@router.post("/collector/v1/servers/{server_id}/host-services/control/{action_id}/result",
    operation_id="report_it_windows_host_service_action",
    response_model=Envelope[HostServiceActionOut])
def report_action(request: Request, server_id: UUID, action_id: UUID,
                  body: HostServiceAgentReportInput,
                  service: HostServiceControl = Depends(get_host_service_control)):
    identity = require_collector_identity(request, required_scopes=(AGENT_SCOPE,))
    result = service.report(
        str(server_id), identity.client_id, str(action_id), body.lease,
        status=body.status, state_after=body.state_after, error_code=body.error_code,
    )
    return ok(result, operation_id="report_it_windows_host_service_action")
