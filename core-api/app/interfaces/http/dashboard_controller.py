# app/interfaces/http/dashboard_controller.py

from flask import Blueprint, jsonify, g

from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.cache.rbac_permission_cache_adapter import RbacCachePermissionCacheAdapter
from app.domain.services.permission_resolver import PermissionResolver
from app.application.use_cases.list_user_apps_use_case import ListUserAppsUseCase


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard/apps", methods=["GET"])
def list_user_apps():

    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    uow = SqlAlchemyUnitOfWork()

    permission_resolver = PermissionResolver(
        permission_query=uow.permission_queries,
        cache=RbacCachePermissionCacheAdapter(),
    )

    use_case = ListUserAppsUseCase(
        app_query=uow.app_queries,
        permission_resolver=permission_resolver,
    )

    result = use_case.execute(
        user_id=user.id,
        is_superadmin=bool(user.is_superadmin),
    )

    return jsonify(result)