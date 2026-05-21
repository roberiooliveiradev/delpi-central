# app/interfaces/http/apps_controller.py

from flask import Blueprint, request, jsonify, g

from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork

from app.application.use_cases.list_admin_apps_use_case import ListAdminAppsUseCase
from app.application.use_cases.update_admin_app_use_case import UpdateAdminAppUseCase

from app.application.use_cases.register_plugin_use_case import RegisterPluginUseCase
from app.application.use_cases.update_plugin_manifest_use_case import UpdatePluginManifestUseCase
from app.application.use_cases.rollback_plugin_version_use_case import RollbackPluginVersionUseCase
from app.application.use_cases.unregister_plugin_use_case import UnregisterPluginUseCase
from app.application.use_cases.get_plugin_manifest_use_case import GetPluginManifestUseCase
from app.application.use_cases.list_plugin_versions_use_case import ListPluginVersionsUseCase

from app.application.use_cases.set_plugin_active_use_case import SetPluginActiveUseCase
from app.application.use_cases.bulk_set_plugins_active_use_case import BulkSetPluginsActiveUseCase
from app.application.use_cases.bulk_unregister_plugins_use_case import BulkUnregisterPluginsUseCase

from app.application.use_cases.list_app_routes_use_case import ListAppRoutesUseCase
from app.application.use_cases.create_app_route_use_case import CreateAppRouteUseCase
from app.application.use_cases.update_route_use_case import UpdateRouteUseCase
from app.application.use_cases.delete_route_use_case import DeleteRouteUseCase
from app.application.use_cases.bulk_delete_routes_use_case import BulkDeleteRoutesUseCase

from app.application.validators.manifest_validator import ManifestValidator

from app.interfaces.http.utils.errors import unauthorized, forbidden, bad_request, not_found

from app.interfaces.http.security.authorization import (
    require_permission,
    require_any_permission,
    require_all_permissions,
    require_superadmin,
    require_auth,
)

admin_apps_bp = Blueprint(
    "admin_apps",
    __name__,
    url_prefix="/admin/apps",
)


def _request_actor() -> tuple[str | None, str | None]:
    user = getattr(g, "current_user", None)
    if not user:
        return None, None
    return str(user.id), getattr(user, "email", None)


# ==========================================================
# LIST APPS (PLUGINS)
# ==========================================================

@admin_apps_bp.get("")
@require_permission("apps.view")
def list_apps():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 10))
    q = request.args.get("q")
    sort = request.args.get("sort", "name")
    direction = request.args.get("direction", "asc")

    with SqlAlchemyUnitOfWork() as uow:
        uc = ListAdminAppsUseCase(uow)

        apps, total = uc.execute(
            page=page,
            page_size=page_size,
            q=q,
            sort=sort,
            direction=direction,
        )

    total_pages = (total + page_size - 1) // page_size

    return jsonify({
        "data": [a.__dict__ for a in apps],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        },
    }), 200


# ==========================================================
# UPDATE APP METADATA
# ==========================================================

@admin_apps_bp.put("/<plugin_id>")
@require_permission("apps.manage")
def update_app(plugin_id: str):
    data = request.get_json(silent=True) or {}

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = UpdateAdminAppUseCase(uow)

            result = uc.execute(
                plugin_id,
                data.get("name"),
                data.get("description"),
                data.get("icon"),
            )

        return jsonify(result), 200

    except Exception as e:
        return bad_request(str(e))


# ==========================================================
# GET MANIFEST
# ==========================================================

@admin_apps_bp.get("/<plugin_id>/manifest")
@require_permission("apps.view")
def get_manifest(plugin_id: str):
    with SqlAlchemyUnitOfWork() as uow:
        uc = GetPluginManifestUseCase(uow)
        result = uc.execute(plugin_id)

    if not result.success:
        return not_found("Manifest not found")

    return jsonify(result.manifest), 200


# ==========================================================
# REGISTER
# ==========================================================

@admin_apps_bp.post("/register")
@require_permission("apps.manage")
def register_plugin():
    manifest = request.get_json(silent=True)

    if not isinstance(manifest, dict):
        return bad_request(
            "Body must be valid JSON",
            code="validation_error",
            path="_global",
        )

    actor_user_id, actor_email = _request_actor()

    try:
        with SqlAlchemyUnitOfWork() as uow:
            validator = ManifestValidator()
            uc = RegisterPluginUseCase(uow, validator)
            result = uc.execute(
                manifest,
                actor_user_id=actor_user_id,
                actor_email=actor_email,
            )

            if not result.success:
                return jsonify({"errors": result.errors}), 400

        return jsonify({"ok": True}), 201

    except Exception as e:
        return bad_request(str(e))


# ==========================================================
# UPDATE MANIFEST
# ==========================================================

@admin_apps_bp.put("/<plugin_id>/manifest")
@require_permission("apps.manage")
def update_manifest(plugin_id: str):
    manifest = request.get_json(silent=True)

    if not isinstance(manifest, dict):
        return bad_request(
            "Body must be valid JSON",
            code="validation_error",
            path="_global",
        )

    actor_user_id, actor_email = _request_actor()

    try:
        with SqlAlchemyUnitOfWork() as uow:
            validator = ManifestValidator()
            uc = UpdatePluginManifestUseCase(uow, validator)
            result = uc.execute(
                plugin_id,
                manifest,
                actor_user_id=actor_user_id,
                actor_email=actor_email,
            )

            if not result.success:
                return jsonify({"errors": result.errors}), 400

        return jsonify({"ok": True}), 200

    except Exception as e:
        return bad_request(str(e))


# ==========================================================
# LIST VERSIONS
# ==========================================================

@admin_apps_bp.get("/<plugin_id>/versions")
@require_permission("apps.manage")
def list_versions(plugin_id: str):
    with SqlAlchemyUnitOfWork() as uow:
        uc = ListPluginVersionsUseCase(uow)
        result = uc.execute(plugin_id)

    if not result.success:
        return jsonify({"errors": result.errors}), 404

    return jsonify(result.versions), 200


# ==========================================================
# ROLLBACK
# ==========================================================

@admin_apps_bp.post("/<plugin_id>/rollback")
@require_permission("apps.manage")
def rollback(plugin_id: str):
    data = request.get_json(silent=True) or {}
    version = data.get("version")

    if not version:
        return bad_request(
            "version is required",
            code="validation_error",
            path="version",
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = RollbackPluginVersionUseCase(uow)
            result = uc.execute(plugin_id, version)

            if not result.success:
                return jsonify({"errors": result.errors}), 400

        return jsonify({"ok": True}), 200

    except Exception as e:
        return bad_request(str(e))


# ==========================================================
# UNREGISTER
# ==========================================================

@admin_apps_bp.delete("/<plugin_id>")
@require_permission("apps.manage")
def unregister(plugin_id: str):
    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = UnregisterPluginUseCase(uow)
            result = uc.execute(plugin_id)

            if not result.success:
                return jsonify({"errors": result.errors}), 400

        return jsonify({"ok": True}), 200

    except Exception as e:
        return bad_request(str(e))


# ==========================================================
# SET ACTIVE
# ==========================================================

@admin_apps_bp.post("/<plugin_id>/active")
@require_permission("apps.manage")
def set_plugin_active(plugin_id: str):
    data = request.get_json(silent=True) or {}
    active = bool(data.get("active", True))

    actor_user_id, actor_email = _request_actor()

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = SetPluginActiveUseCase(uow)
            result = uc.execute(
                plugin_id,
                active,
                actor_user_id=actor_user_id,
                actor_email=actor_email,
            )

            if not result.success:
                return jsonify({"errors": result.errors}), 400

        return jsonify({"ok": True}), 200

    except Exception as e:
        return bad_request(str(e))


# ==========================================================
# BULK ACTIVATE / DEACTIVATE
# ==========================================================

@admin_apps_bp.post("/bulk-activate")
@require_permission("apps.manage")
def bulk_activate_plugins():
    data = request.get_json(silent=True) or {}
    ids = data.get("ids", [])
    active = bool(data.get("active", True))

    if not isinstance(ids, list):
        return bad_request(
            "ids must be a list",
            code="validation_error",
            path="ids",
        )

    actor_user_id, actor_email = _request_actor()

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = BulkSetPluginsActiveUseCase(uow)
            result = uc.execute(
                ids,
                active,
                actor_user_id=actor_user_id,
                actor_email=actor_email,
            )

            if not result.success:
                return jsonify({"errors": result.errors}), 400

        return jsonify({"ok": True, "updated": result.updated}), 200

    except Exception as e:
        return bad_request(str(e))


# ==========================================================
# BULK UNREGISTER
# ==========================================================

@admin_apps_bp.post("/bulk-unregister")
@require_permission("apps.manage")
def bulk_unregister():
    data = request.get_json(silent=True) or {}
    ids = data.get("ids", [])

    if not isinstance(ids, list):
        return bad_request(
            "ids must be a list",
            code="validation_error",
            path="ids",
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = BulkUnregisterPluginsUseCase(uow)
            result = uc.execute(ids)

            if not result.success:
                return jsonify({"errors": result.errors}), 400

        return jsonify({"ok": True, "deleted": result.deleted}), 200

    except Exception as e:
        return bad_request(str(e))


# ==========================================================
# LIST ROUTES
# ==========================================================

@admin_apps_bp.get("/<app_id>/routes")
@require_permission("apps.view")
def list_routes(app_id: str):
    with SqlAlchemyUnitOfWork() as uow:
        uc = ListAppRoutesUseCase(uow)
        result = uc.execute(app_id)

    if not result.success:
        return jsonify({"errors": result.errors}), 400

    return jsonify(result.routes), 200


# ==========================================================
# CREATE ROUTE
# ==========================================================

@admin_apps_bp.post("/<app_id>/routes")
@require_permission("apps.manage")
def create_route(app_id: str):
    data = request.get_json(silent=True) or {}

    required = ["path", "label", "icon", "order"]
    missing = [k for k in required if data.get(k) in (None, "")]

    if missing:
        return bad_request(
            f"Missing fields: {', '.join(missing)}",
            code="validation_error",
            path="_global",
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = CreateAppRouteUseCase(uow)

            result = uc.execute(
                app_id,
                path=str(data.get("path")),
                label=str(data.get("label")),
                icon=str(data.get("icon")),
                permission_code=(
                    data.get("permissionCode")
                    or data.get("permission_code")
                    or None
                ),
                order=int(data.get("order")),
                show_in_menu=bool(
                    data.get(
                        "showInMenu",
                        data.get("show_in_menu", True),
                    )
                ),
                active=bool(data.get("active", True)),
            )

        if not result.success:
            return jsonify({"errors": result.errors}), 400

        return jsonify(result.route), 201

    except Exception as e:
        return jsonify({
            "errors": [{
                "code": "route.create_failed",
                "message": str(e),
                "path": "_global",
            }]
        }), 400


# ==========================================================
# UPDATE ROUTE
# ==========================================================

@admin_apps_bp.put("/routes/<route_id>")
@require_permission("apps.manage")
def update_route(route_id: str):
    data = request.get_json(silent=True) or {}

    patch = {}

    if "path" in data:
        patch["path"] = data["path"]

    if "label" in data:
        patch["label"] = data["label"]

    if "icon" in data:
        patch["icon"] = data["icon"]

    if "order" in data:
        patch["order"] = data["order"]

    if "showInMenu" in data:
        patch["show_in_menu"] = data["showInMenu"]

    if "active" in data:
        patch["active"] = data["active"]

    if "permissionCode" in data:
        patch["permission_code"] = data["permissionCode"]

    if not patch:
        return bad_request(
            "No fields to update",
            code="validation_error",
            path="_global",
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = UpdateRouteUseCase(uow)
            result = uc.execute(route_id, patch)

        if not result.success:
            return jsonify({"errors": result.errors}), 400

        return jsonify({"ok": True}), 200

    except Exception as e:
        return jsonify({
            "errors": [{
                "code": "route.update_failed",
                "message": str(e),
                "path": "_global",
            }]
        }), 400


# ==========================================================
# DELETE ROUTE
# ==========================================================

@admin_apps_bp.delete("/routes/<route_id>")
@require_permission("apps.manage")
def delete_route(route_id: str):
    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = DeleteRouteUseCase(uow)
            result = uc.execute(route_id)

        if not result.success:
            return jsonify({"errors": result.errors}), 400

        return jsonify({"ok": True}), 200

    except Exception as e:
        return jsonify({
            "errors": [{
                "code": "route.delete_failed",
                "message": str(e),
                "path": "_global",
            }]
        }), 400


# ==========================================================
# BULK DELETE ROUTES
# ==========================================================

@admin_apps_bp.post("/routes/bulk-delete")
@require_permission("apps.manage")
def bulk_delete_routes():
    data = request.get_json(silent=True) or {}

    ids = data.get("ids") or data.get("routeIds") or []

    if not isinstance(ids, list) or not ids:
        return bad_request(
            "ids must be a non-empty list",
            code="validation_error",
            path="ids",
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = BulkDeleteRoutesUseCase(uow)
            result = uc.execute([str(x) for x in ids])

        if not result.success:
            return jsonify({"errors": result.errors}), 400

        return jsonify({
            "ok": True,
            "deleted": result.deleted,
        }), 200

    except Exception as e:
        return jsonify({
            "errors": [{
                "code": "route.bulk_delete_failed",
                "message": str(e),
                "path": "_global",
            }]
        }), 400