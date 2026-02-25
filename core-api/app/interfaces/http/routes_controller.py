# app/interfaces/http/routes_controller.py

from flask import Blueprint, request, jsonify, g

from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.application.use_cases.list_app_routes_use_case import ListAppRoutesUseCase
from app.application.use_cases.create_app_route_use_case import CreateAppRouteUseCase
from app.application.use_cases.update_route_use_case import UpdateRouteUseCase
from app.application.use_cases.delete_route_use_case import DeleteRouteUseCase
from app.application.use_cases.bulk_delete_routes_use_case import BulkDeleteRoutesUseCase

from app.interfaces.http.utils.errors import unauthorized, forbidden, bad_request


admin_routes_bp = Blueprint("admin_routes", __name__, url_prefix="/admin")


def require_admin():
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()
    if getattr(user, "is_superadmin", False):
        return None
    return forbidden("Forbidden")


@admin_routes_bp.get("/apps/<app_id>/routes")
def list_routes(app_id: str):
    guard = require_admin()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = ListAppRoutesUseCase(uow)
    result = uc.execute(app_id)

    if not result.success:
        return jsonify({"errors": result.errors}), 400

    return jsonify(result.routes), 200


@admin_routes_bp.post("/apps/<app_id>/routes")
def create_route(app_id: str):
    guard = require_admin()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    required = ["path", "label", "icon", "order"]
    missing = [k for k in required if data.get(k) in (None, "")]
    if missing:
        return bad_request(f"Missing fields: {', '.join(missing)}", code="validation_error", path="_global")

    uow = SqlAlchemyUnitOfWork()
    uc = CreateAppRouteUseCase(uow)
    result = uc.execute(
        app_id,
        path=str(data.get("path")),
        label=str(data.get("label")),
        icon=str(data.get("icon")),
        permission_code=(data.get("permissionCode") or data.get("permission_code") or None),
        order=int(data.get("order")),
        show_in_menu=bool(data.get("showInMenu", data.get("show_in_menu", True))),
        active=bool(data.get("active", True)),
    )

    if not result.success:
        return jsonify({"errors": result.errors}), 400

    return jsonify(result.route), 201


@admin_routes_bp.put("/routes/<route_id>")
def update_route(route_id: str):
    guard = require_admin()
    if guard:
        return guard

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
        return bad_request("No fields to update", code="validation_error", path="_global")

    uow = SqlAlchemyUnitOfWork()
    uc = UpdateRouteUseCase(uow)
    result = uc.execute(route_id, patch)

    if not result.success:
        return jsonify({"errors": result.errors}), 400

    return jsonify({"ok": True}), 200


@admin_routes_bp.delete("/routes/<route_id>")
def delete_route(route_id: str):
    guard = require_admin()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = DeleteRouteUseCase(uow)
    result = uc.execute(route_id)

    if not result.success:
        return jsonify({"errors": result.errors}), 400

    return jsonify({"ok": True}), 200


@admin_routes_bp.post("/routes/bulk-delete")
def bulk_delete_routes():
    guard = require_admin()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    ids = data.get("ids") or data.get("routeIds") or []

    if not isinstance(ids, list) or not ids:
        return bad_request("ids must be a non-empty list", code="validation_error", path="ids")

    uow = SqlAlchemyUnitOfWork()
    uc = BulkDeleteRoutesUseCase(uow)
    result = uc.execute([str(x) for x in ids])

    if not result.success:
        return jsonify({"errors": result.errors}), 400

    return jsonify({"ok": True, "deleted": result.deleted}), 200