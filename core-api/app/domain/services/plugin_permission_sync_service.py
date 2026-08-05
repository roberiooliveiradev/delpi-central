# app/domain/services/plugin_permission_sync_service.py

from __future__ import annotations

from typing import Any, Dict, List, Mapping


class PluginPermissionSyncService:
    """
    Sync declarativo de permissions de plugin por `code`.

    Identidade estável = code (+ module). Usado por register e rollback
    para não destruir UUIDs (e portanto role_permissions / user_permissions)
    quando o code permanece no manifesto.
    """

    @staticmethod
    def normalize_desired(
        module: str,
        permissions: List[Mapping[str, Any]] | None,
    ) -> List[Dict[str, Any]]:
        desired: List[Dict[str, Any]] = []
        seen: set[str] = set()

        for raw in permissions or []:
            code = str(raw.get("code") or "").strip()
            if not code or code in seen:
                continue
            seen.add(code)
            name = str(raw.get("name") or code).strip() or code
            description = raw.get("description")
            if description is not None:
                description = str(description)
            desired.append(
                {
                    "code": code,
                    "name": name,
                    "description": description,
                    "module": module,
                }
            )

        return desired
