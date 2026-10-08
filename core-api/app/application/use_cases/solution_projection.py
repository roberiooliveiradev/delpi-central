"""Safe solution projection — shared contract for the discovery surface.

Core owns visibility: any authenticated user may discover safe metadata
of ACTIVE registered apps. SOLUTION VISIBILITY != ACCESS AUTHORIZATION —
the ``accessible`` flag is computed by AppAuthorizationService and never
grants anything.

Never exposed: backend/security/healthcheck/observability/entry/metadata
manifest blocks, actor identities (created_by/updated_by), permission
UUIDs, checksums, user-level RBAC graph.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.domain.ports.app_query_port import AppDTO


def _serialize_routes(app: AppDTO) -> List[Dict[str, Any]]:
    return [
        {
            "path": r.path,
            "label": r.label,
            "icon": r.icon,
            "order": r.order,
            "showInMenu": bool(r.show_in_menu),
        }
        for r in app.routes
    ]


def _serialize_permissions(manifest: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Permission code+name+description — functional capability knowledge.

    Codes are already exposed to authenticated users via /me/apps route
    payloads; ids and the role/group graph stay internal.
    """
    if not manifest:
        return []
    return [
        {
            "code": p.get("code"),
            "name": p.get("name"),
            "description": p.get("description"),
        }
        for p in manifest.get("permissions") or []
        if p.get("code")
    ]


def serialize_solution(
    app: AppDTO,
    plugin_row,
    manifest: Optional[Dict[str, Any]],
    *,
    accessible: bool,
) -> Dict[str, Any]:
    manifest = manifest or {}
    description = getattr(plugin_row, "description", None) or manifest.get("description")
    return {
        "id": app.id,
        "name": app.name,
        "description": description,
        "icon": app.icon,
        "type": app.type,
        "category": manifest.get("category"),
        "version": getattr(plugin_row, "version", None) or manifest.get("version"),
        "active": bool(getattr(plugin_row, "active", True)),
        "basePath": app.base_path,
        "routes": _serialize_routes(app),
        "features": manifest.get("features"),
        "permissions": _serialize_permissions(manifest),
        "dependencies": manifest.get("dependencies") or [],
        "accessible": accessible,
        "updatedAt": (
            plugin_row.updated_at.isoformat()
            if getattr(plugin_row, "updated_at", None)
            else None
        ),
    }


def serialize_version(row: Dict[str, Any]) -> Dict[str, Any]:
    """Public version entry — internal persistence fields never leave Core."""
    return {
        "version": row.get("version"),
        "created_at": row.get("created_at"),
    }


def diff_manifests(
    current: Optional[Dict[str, Any]],
    previous: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Structural diff between two manifest snapshots — CALCULATED.

    Reports what changed structurally; never infers reason, benefit or
    release purpose (UNKNOWN without an explicit source).
    """
    cur = current or {}
    prev = previous or {}

    def route_paths(m: Dict[str, Any]) -> set:
        return {r.get("path") for r in m.get("routes") or [] if r.get("path")}

    def permission_codes(m: Dict[str, Any]) -> set:
        return {p.get("code") for p in m.get("permissions") or [] if p.get("code")}

    cur_routes, prev_routes = route_paths(cur), route_paths(prev)
    cur_perms, prev_perms = permission_codes(cur), permission_codes(prev)

    cur_features = cur.get("features") or {}
    prev_features = prev.get("features") or {}

    return {
        "basis": "CALCULATED",
        "versionChanged": cur.get("version") != prev.get("version"),
        "descriptionChanged": cur.get("description") != prev.get("description"),
        "routesAdded": sorted(cur_routes - prev_routes),
        "routesRemoved": sorted(prev_routes - cur_routes),
        "permissionsAdded": sorted(cur_perms - prev_perms),
        "permissionsRemoved": sorted(prev_perms - cur_perms),
        "featuresChanged": cur_features != prev_features,
    }
