"""Visão geral, capabilities do usuário e health."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from it_portal_app.application.dashboard_service import DashboardService
from it_portal_app.core.responses import ok
from it_portal_app.interface.http.authz import (
    ACTIONS_MANAGE,
    ACTIONS_VIEW,
    DATABASES_MANAGE,
    DATABASES_VIEW,
    INTEGRATIONS_MANAGE,
    INTEGRATIONS_VIEW,
    NETWORKS_MANAGE,
    NETWORKS_VIEW,
    NOTES_CREATE,
    SERVERS_MANAGE,
    HOST_SERVICES_MANAGE,
    HOST_SERVICES_CONTROL,
    SERVERS_VIEW,
    SERVICES_MANAGE,
    SERVICES_VIEW,
    COMPUTERS_VIEW,
    COMPUTERS_MANAGE,
    actor_from,
    authorize,
    user_has,
)
from it_portal_app.interface.http.dependencies import get_dashboard_service
from it_portal_app.interface.http.schemas import (
    ERROR_RESPONSES,
    CapabilitiesOut,
    DashboardOut,
    Envelope,
    HealthOut,
)

router = APIRouter()


@router.get(
    "/health",
    operation_id="get_it_portal_health",
    response_model=HealthOut,
    tags=["Health"],
    summary="Liveness — sem dados do inventário",
)
def get_it_portal_health():
    return {"status": "online", "service": "it-portal-api"}


@router.get(
    "/me/capabilities",
    operation_id="get_it_portal_capabilities",
    response_model=Envelope[CapabilitiesOut],
    tags=["Me"],
    responses=ERROR_RESPONSES,
    summary="Capabilities efetivas do usuário no Portal de TI (decididas pelo backend)",
)
def get_it_portal_capabilities(request: Request):
    user = authorize(request)
    view_servers = user_has(user, SERVERS_VIEW)
    view_services = view_servers and user_has(user, SERVICES_VIEW)
    view_databases = view_servers and user_has(user, DATABASES_VIEW)
    view_networks = view_servers and user_has(user, NETWORKS_VIEW)
    view_integrations = view_services and user_has(user, INTEGRATIONS_VIEW)
    data = {
        "display_name": actor_from(user).name,
        "can_view_servers": view_servers,
        "can_manage_servers": view_servers and user_has(user, SERVERS_MANAGE),
        "can_view_computers": user_has(user, COMPUTERS_VIEW),
        "can_manage_computers": user_has(user, COMPUTERS_VIEW) and user_has(user, COMPUTERS_MANAGE),
        "can_manage_host_services": view_servers and user_has(user, HOST_SERVICES_MANAGE),
        "can_control_host_services": view_servers and user_has(user, HOST_SERVICES_CONTROL),
        "can_create_notes": view_servers and user_has(user, NOTES_CREATE),
        "can_view_action_plans": view_servers and user_has(user, ACTIONS_VIEW),
        "can_manage_action_plans": view_servers and user_has(user, ACTIONS_MANAGE),
        "can_view_services": view_services,
        "can_manage_services": view_services and user_has(user, SERVICES_MANAGE),
        "can_view_databases": view_databases,
        "can_manage_databases": view_databases and user_has(user, DATABASES_MANAGE),
        "can_view_networks": view_networks,
        "can_manage_networks": view_networks and user_has(user, NETWORKS_MANAGE),
        "can_view_integrations": view_integrations,
        "can_manage_integrations": view_integrations and user_has(user, INTEGRATIONS_MANAGE),
    }
    return ok(data, operation_id="get_it_portal_capabilities")


@router.get(
    "/dashboard",
    operation_id="get_it_portal_dashboard",
    response_model=Envelope[DashboardOut],
    tags=["Overview"],
    responses=ERROR_RESPONSES,
    summary="Indicadores e listas da visão geral",
)
def get_it_portal_dashboard(
    request: Request,
    service: DashboardService = Depends(get_dashboard_service),
):
    user = authorize(request, SERVERS_VIEW)
    data = service.overview(include_action_plans=user_has(user, ACTIONS_VIEW))
    return ok(data, operation_id="get_it_portal_dashboard")
