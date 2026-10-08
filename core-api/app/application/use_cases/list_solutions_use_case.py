# app/application/use_cases/list_solutions_use_case.py

from typing import Any, Dict, List

from app.application.services.app_authorization_service import (
    AppAuthorizationService,
)
from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.solution_projection import serialize_solution


class ListSolutionsUseCase:
    """Authenticated discovery of safe solution metadata.

    Unlike ``/me/apps`` (access-filtered) and ``/admin/apps`` (admin
    permission), this lists every ACTIVE app with an ``accessible`` flag —
    Core-owned visibility policy, never a grant.
    """

    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self._authz = AppAuthorizationService()

    def execute(
        self,
        *,
        permissions: List[str],
        is_superadmin: bool,
    ) -> List[Dict[str, Any]]:
        apps = self._uow.app_queries.list_active_apps_with_routes()
        accessible_ids = self._authz.filter_app_ids(
            apps=apps,
            permissions=permissions,
            is_superadmin=is_superadmin,
        )

        manifests = {
            row["app_id"]: row["manifest"]
            for row in self._uow.plugin_manifests.list_all()
        }

        return [
            serialize_solution(
                app,
                self._uow.plugins.get_by_id(app.id),
                manifests.get(app.id),
                accessible=app.id in accessible_ids,
            )
            for app in apps
        ]
