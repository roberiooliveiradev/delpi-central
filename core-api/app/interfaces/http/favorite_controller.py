# app/interfaces/http/favorite_controller.py

from flask import Blueprint, jsonify, g, request

from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.application.use_cases.list_favorite_apps_use_case import ListFavoriteAppsUseCase
from app.application.use_cases.add_favorite_app_use_case import AddFavoriteAppUseCase
from app.application.use_cases.remove_favorite_app_use_case import RemoveFavoriteAppUseCase


favorite_bp = Blueprint("favorites", __name__)


@favorite_bp.route("/favorites", methods=["GET"])
def list_favorites():
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    uow = SqlAlchemyUnitOfWork()
    use_case = ListFavoriteAppsUseCase(uow.favorite_apps)

    result = use_case.execute(user_id=str(user.id))

    return jsonify(result)


@favorite_bp.route("/favorites/<app_id>", methods=["POST"])
def add_favorite(app_id: str):
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    uow = SqlAlchemyUnitOfWork()
    use_case = AddFavoriteAppUseCase(uow)

    use_case.execute(str(user.id), app_id)

    return jsonify({"ok": True})


@favorite_bp.route("/favorites/<app_id>", methods=["DELETE"])
def remove_favorite(app_id: str):
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    uow = SqlAlchemyUnitOfWork()
    use_case = RemoveFavoriteAppUseCase(uow)

    use_case.execute(str(user.id), app_id)

    return jsonify({"ok": True})