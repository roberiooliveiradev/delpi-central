from flask import Blueprint, jsonify

from app.application.use_cases.health_check_use_case import HealthCheckUseCase
from app.application.use_cases.ready_check_use_case import ReadyCheckUseCase

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    return jsonify(HealthCheckUseCase().execute()), 200


@health_bp.get("/ready")
def ready():
    return jsonify(ReadyCheckUseCase().execute()), 200
