"""Composição dos casos de uso com o adapter de persistência."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from fastapi import Depends

from it_portal_app.application.action_plan_service import ActionPlanService
from it_portal_app.application.clock import business_today
from it_portal_app.application.dashboard_service import DashboardService
from it_portal_app.application.ports import ItPortalRepository
from it_portal_app.application.server_service import ServerService
from it_portal_app.infrastructure.persistence.postgres_repository import (
    PostgresItPortalRepository,
)


def get_repository() -> ItPortalRepository:
    return PostgresItPortalRepository()


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
