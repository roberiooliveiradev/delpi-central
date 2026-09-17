from flask import Blueprint, current_app, jsonify

from app.application.health import build_liveness_status

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    payload = build_liveness_status(
        service_name=current_app.config["SERVICE_NAME"],
        service_version=current_app.config["SERVICE_VERSION"],
    )
    return jsonify(payload), 200
