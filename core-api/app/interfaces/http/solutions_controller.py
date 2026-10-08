# app/interfaces/http/solutions_controller.py
"""Authenticated solution discovery — safe projection of the app catalog.

Core is the authority for apps/plugins/manifests/versions. Visibility
policy: any authenticated user may discover ACTIVE apps' safe metadata;
``accessible`` reports effective access without granting it.
"""

from flask import Blueprint, jsonify, g

from app.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from app.application.use_cases.list_solutions_use_case import (
    ListSolutionsUseCase,
)
from app.application.use_cases.get_solution_use_case import (
    GetSolutionUseCase,
)
from app.interfaces.http.security.authorization import require_auth
from app.interfaces.http.utils.errors import not_found


solutions_bp = Blueprint(
    "solutions",
    __name__,
    url_prefix="/solutions",
)


def _user_context():
    user = g.current_user
    return getattr(user, "permissions", None) or [], bool(
        getattr(user, "is_superadmin", False)
    )


@solutions_bp.get("")
@require_auth()
def list_solutions():
    permissions, is_superadmin = _user_context()
    with SqlAlchemyUnitOfWork() as uow:
        result = ListSolutionsUseCase(uow).execute(
            permissions=permissions,
            is_superadmin=is_superadmin,
        )
    return jsonify({"data": result}), 200


@solutions_bp.get("/<plugin_id>")
@require_auth()
def get_solution(plugin_id: str):
    permissions, is_superadmin = _user_context()
    with SqlAlchemyUnitOfWork() as uow:
        result = GetSolutionUseCase(uow).execute(
            plugin_id,
            permissions=permissions,
            is_superadmin=is_superadmin,
        )
    if result is None:
        return not_found("Solution not found")
    return jsonify({"data": result}), 200
