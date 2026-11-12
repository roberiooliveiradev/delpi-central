"""Composição dos casos de uso com o adapter de persistência."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from fastapi import Depends

from it_portal_app.application.action_plan_service import ActionPlanService
from it_portal_app.application.clock import business_today
from it_portal_app.application.dashboard_service import DashboardService
from it_portal_app.application.database_inventory import DatabaseInventory
from it_portal_app.application.integration_inventory import IntegrationInventory
from it_portal_app.application.network_inventory import NetworkInventory
from it_portal_app.application.observation_service import ObservationService
from it_portal_app.application.host_service_inventory import HostServiceInventory
from it_portal_app.application.host_service_control import HostServiceControl
from it_portal_app.application.ports import (
    ConnectivityRepository,
    InventoryRepository,
    ItPortalRepository,
    ObservationRepository,
)
from it_portal_app.application.server_service import ServerService
from it_portal_app.application.service_inventory import ServiceInventory
from it_portal_app.infrastructure.persistence.postgres_connectivity_repository import (
    PostgresConnectivityRepository,
)
from it_portal_app.infrastructure.persistence.postgres_inventory_repository import (
    PostgresInventoryRepository,
)
from it_portal_app.infrastructure.persistence.postgres_host_service_repository import PostgresHostServiceRepository
from it_portal_app.infrastructure.persistence.postgres_host_service_actions import PostgresHostServiceActions
from it_portal_app.infrastructure.persistence.postgres_observation_repository import (
    PostgresObservationRepository,
)
from it_portal_app.infrastructure.persistence.postgres_repository import (
    PostgresItPortalRepository,
)


def get_repository() -> ItPortalRepository:
    return PostgresItPortalRepository()


def get_inventory_repository() -> InventoryRepository:
    return PostgresInventoryRepository()


def get_service_inventory(
    inventory: InventoryRepository = Depends(get_inventory_repository),
    servers: ItPortalRepository = Depends(get_repository),
) -> ServiceInventory:
    return ServiceInventory(inventory, servers)


def get_database_inventory(
    inventory: InventoryRepository = Depends(get_inventory_repository),
    servers: ItPortalRepository = Depends(get_repository),
) -> DatabaseInventory:
    return DatabaseInventory(inventory, servers)


def get_connectivity_repository() -> ConnectivityRepository:
    return PostgresConnectivityRepository()


def get_network_inventory(
    connectivity: ConnectivityRepository = Depends(get_connectivity_repository),
    inventory: InventoryRepository = Depends(get_inventory_repository),
    servers: ItPortalRepository = Depends(get_repository),
) -> NetworkInventory:
    return NetworkInventory(connectivity, inventory, servers)


def get_integration_inventory(
    connectivity: ConnectivityRepository = Depends(get_connectivity_repository),
    inventory: InventoryRepository = Depends(get_inventory_repository),
    servers: ItPortalRepository = Depends(get_repository),
) -> IntegrationInventory:
    return IntegrationInventory(connectivity, inventory, servers)


def get_today_provider() -> Callable[[], date]:
    return business_today


def get_server_service(
    repository: ItPortalRepository = Depends(get_repository),
) -> ServerService:
    return ServerService(repository)


def get_action_plan_service(
    repository: ItPortalRepository = Depends(get_repository),
    today: Callable[[], date] = Depends(get_today_provider),
) -> ActionPlanService:
    return ActionPlanService(repository, today)


def get_dashboard_service(
    repository: ItPortalRepository = Depends(get_repository),
    today: Callable[[], date] = Depends(get_today_provider),
) -> DashboardService:
    return DashboardService(repository, today)


def get_observation_repository() -> ObservationRepository:
    return PostgresObservationRepository()


def get_observation_service(
    observations: ObservationRepository = Depends(get_observation_repository),
    servers: ItPortalRepository = Depends(get_repository),
) -> ObservationService:
    return ObservationService(observations, servers)


def get_host_service_inventory(servers: ItPortalRepository = Depends(get_repository)) -> HostServiceInventory:
    return HostServiceInventory(PostgresHostServiceRepository(), servers)


def get_host_service_control(servers: ItPortalRepository = Depends(get_repository)) -> HostServiceControl:
    return HostServiceControl(PostgresHostServiceActions(), servers)
