# app/interfaces/http/plugins_controller.py

from flask import Blueprint, request, jsonify, g
from app.application.use_cases.register_plugin_use_case import register_plugin, PluginRegistrationError
from app.domain.services.plugin_manifest_validator import ManifestValidationError

plugins_bp = Blueprint("plugins", __name__, url_prefix="/core-api/plugins")


@plugins_bp.route("/register", methods=["POST"])
def register():
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    manifest = request.get_json(silent=True)
    if not isinstance(manifest, dict):
        return jsonify({"error": "Body deve ser JSON"}), 400

    try:
        result = register_plugin(
            manifest=manifest,
            actor_user_id=str(user.id),
            ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
        )
        return jsonify({
            "status": "ok",
            "appId": result.app_id,
            "created": result.created,
            "version": result.version
        }), 201

    except ManifestValidationError as e:
        return jsonify({"error": str(e)}), 400
    except PluginRegistrationError as e:
        return jsonify({"error": str(e)}), 409
