from flask import Blueprint, jsonify

from app.application.use_cases.health_check_use_case import HealthCheckUseCase

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    result = HealthCheckUseCase().execute()
    return jsonify(result), 200
