# app/interfaces/http/apps_controller.py

from flask import Blueprint, request, jsonify, g

from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.application.use_cases.list_admin_apps_use_case import ListAdminAppsUseCase
from app.application.use_cases.update_admin_app_use_case import UpdateAdminAppUseCase
from app.application.use_cases.set_app_active_use_case import SetAppActiveUseCase
from app.application.use_cases.delete_admin_app_use_case import DeleteAdminAppUseCase
from app.interfaces.http.utils.errors import unauthorized, api_error


admin_apps_bp = Blueprint("admin_apps", __name__)


@admin_apps_bp.route("/admin/apps", methods=["GET"])
def list_apps():
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()

    # parâmetros
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 10))
    q = request.args.get("q")
    sort = request.args.get("sort", "name")
    direction = request.args.get("direction", "asc")

    uow = SqlAlchemyUnitOfWork()
    use_case = ListAdminAppsUseCase(uow)

    apps, total = use_case.execute(
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
        }
    })


@admin_apps_bp.route("/admin/apps/<app_id>", methods=["PUT"])
def update_app(app_id: str):
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()

    data = request.get_json(silent=True) or {}

    uow = SqlAlchemyUnitOfWork()
    use_case = UpdateAdminAppUseCase(uow)

    try:
        return jsonify(
            use_case.execute(
                app_id,
                data.get("name"),
                data.get("description"),
                data.get("icon"),
            )
        )
    except Exception as e:
        uow.rollback()
        return api_error("update_app_failed", str(e))


@admin_apps_bp.route("/admin/apps/<app_id>/active", methods=["POST"])
def set_app_active(app_id: str):
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()

    data = request.get_json(silent=True) or {}
    active = bool(data.get("active", True))

    uow = SqlAlchemyUnitOfWork()
    use_case = SetAppActiveUseCase(uow)

    try:
        return jsonify(use_case.execute(app_id, active))
    except Exception as e:
        uow.rollback()
        return api_error("set_app_active_failed", str(e))


@admin_apps_bp.route("/admin/apps/<app_id>", methods=["DELETE"])
def delete_app(app_id: str):
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()

    uow = SqlAlchemyUnitOfWork()
    use_case = DeleteAdminAppUseCase(uow)

    try:
        return jsonify(use_case.execute(app_id))
    except Exception as e:
        uow.rollback()
        return api_error("delete_app_failed", str(e))