# app/application/use_cases/get_solution_use_case.py

from typing import Any, Dict, List, Optional

from app.application.services.app_authorization_service import (
    AppAuthorizationService,
)
from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.solution_projection import (
    diff_manifests,
    serialize_solution,
    serialize_version,
)

RECENT_VERSIONS_LIMIT = 5


class GetSolutionUseCase:
    """Single-solution detail: safe projection + recent evolution.

    Evolution is a structural manifest diff — CALCULATED from PROVEN
    snapshots. No inferred release purpose.
    """

    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self._authz = AppAuthorizationService()

    def execute(
        self,
        plugin_id: str,
        *,
        permissions: List[str],
        is_superadmin: bool,
    ) -> Optional[Dict[str, Any]]:
        apps = self._uow.app_queries.list_active_apps_with_routes()
        app = next((a for a in apps if a.id == plugin_id), None)
        if app is None:
            return None

        accessible_ids = self._authz.filter_app_ids(
            apps=apps,
            permissions=permissions,
            is_superadmin=is_superadmin,
        )

        manifest = self._uow.plugin_manifests.get(plugin_id)
        payload = serialize_solution(
            app,
            self._uow.plugins.get_by_id(plugin_id),
            manifest,
            accessible=plugin_id in accessible_ids,
        )

        versions = self._uow.plugin_versions.list_versions(plugin_id)
        # INTERNAL CALCULATION INPUT != PUBLIC PROJECTION: raw rows keep
        # checksum/snapshot internals for the evolution diff; the public
        # recentVersions surface goes through serialize_version.
        payload["recentVersions"] = [
            serialize_version(v) for v in versions[:RECENT_VERSIONS_LIMIT]
        ]

        evolution: Optional[Dict[str, Any]] = None
        if versions:
            current_snapshot = self._uow.plugin_versions.get_version(
                plugin_id, versions[0]["version"]
            )
            previous_snapshot = (
                self._uow.plugin_versions.get_version(
                    plugin_id, versions[1]["version"]
                )
                if len(versions) > 1
                else None
            )
            evolution = {
                "fromVersion": previous_snapshot["version"] if previous_snapshot else None,
                "toVersion": current_snapshot["version"] if current_snapshot else None,
                **diff_manifests(
                    (current_snapshot or {}).get("manifest"),
                    (previous_snapshot or {}).get("manifest"),
                ),
            }
        payload["evolution"] = evolution

        return payload
