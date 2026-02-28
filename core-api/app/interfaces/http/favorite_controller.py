# app/interfaces/http/favorite_controller.py

from flask import Blueprint, jsonify, g

from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork

from app.application.use_cases.list_favorite_apps_use_case import ListFavoriteAppsUseCase
from app.application.use_cases.add_favorite_app_use_case import AddFavoriteAppUseCase
from app.application.use_cases.remove_favorite_app_use_case import RemoveFavoriteAppUseCase

from app.interfaces.http.utils.errors import unauthorized


favorite_bp = Blueprint("favorites", __name__)


def require_auth():
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()
    return None


# ---------------------------------------------------------
# GET /favorites
# ---------------------------------------------------------

@favorite_bp.route("/favorites", methods=["GET"])
def list_favorites():
    guard = require_auth()
    if guard:
        return guard

    with SqlAlchemyUnitOfWork() as uow:
        use_case = ListFavoriteAppsUseCase(uow)
        result = use_case.execute(
            user_id=str(g.current_user.id)
        )

    return jsonify(result), 200


# ---------------------------------------------------------
# POST /favorites/<app_id>
# ---------------------------------------------------------

@favorite_bp.route("/favorites/<app_id>", methods=["POST"])
def add_favorite(app_id: str):
    guard = require_auth()
    if guard:
        return guard

    with SqlAlchemyUnitOfWork() as uow:
        use_case = AddFavoriteAppUseCase(uow)

        use_case.execute(
            user_id=str(g.current_user.id),
            app_id=app_id,
        )

    return jsonify({"ok": True}), 200


# ---------------------------------------------------------
# DELETE /favorites/<app_id>
# ---------------------------------------------------------

@favorite_bp.route("/favorites/<app_id>", methods=["DELETE"])
def remove_favorite(app_id: str):
    guard = require_auth()
    if guard:
        return guard

    with SqlAlchemyUnitOfWork() as uow:
        use_case = RemoveFavoriteAppUseCase(uow)

        use_case.execute(
            user_id=str(g.current_user.id),
            app_id=app_id,
        )

    return jsonify({"ok": True}), 200


# =========================================================
# Compatibilidade com frontend antigo
# =========================================================

@favorite_bp.route("/me/apps/favorites", methods=["GET"])
def list_favorites_me():
    return list_favorites()


@favorite_bp.route("/me/apps/favorites/<app_id>", methods=["POST"])
def add_favorite_me(app_id: str):
    return add_favorite(app_id)


@favorite_bp.route("/me/apps/favorites/<app_id>", methods=["DELETE"])
def remove_favorite_me(app_id: str):
    return remove_favorite(app_id)