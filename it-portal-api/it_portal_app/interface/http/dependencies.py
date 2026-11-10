"""Composição dos casos de uso com o adapter de persistência."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from fastapi import Depends

from it_portal_app.application.action_plan_service import ActionPlanService
from it_portal_app.application.clock import business_today
from it_portal_app.application.dashboard_service import DashboardService
from it_portal_app.application.database_inventory import DatabaseInventory
from it_portal_app.application.ports import InventoryRepository, ItPortalRepository
from it_portal_app.application.server_service import ServerService
from it_portal_app.application.service_inventory import ServiceInventory
from it_portal_app.infrastructure.persistence.postgres_inventory_repository import (
    PostgresInventoryRepository,
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
