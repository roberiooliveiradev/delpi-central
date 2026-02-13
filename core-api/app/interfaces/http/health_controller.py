# app/interfaces/http/health_controller.py

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "Api rodando!"}), 200
