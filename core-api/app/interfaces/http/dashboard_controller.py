# app/interfaces/http/dashboard_controller.py

from flask import Blueprint, jsonify, g
from app.domain.services.permission_resolver import resolve_user_permissions
from app.domain.services.app_resolver import resolve_user_apps

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard", methods=["GET"])
def dashboard():

    user = getattr(g, "current_user", None)

    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    # Permissões efetivas do usuário
    permissions = resolve_user_permissions(user)

    # Apps que o usuário realmente pode acessar
    user_apps = resolve_user_apps(permissions)

    return jsonify({
        "appsCount": len(user_apps),
        "rolesCount": len(user.roles),
        "permissionsCount": len(permissions),
        "recentActivity": [
            "Login realizado com sucesso",
            f"{len(permissions)} permissões carregadas",
            f"{len(user_apps)} aplicações disponíveis"
        ]
    })
