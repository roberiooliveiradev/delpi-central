from flask import Blueprint, g, jsonify

from app.application.services.home_attention_service import HomeAttentionService
from app.interfaces.http.auth_decorators import require_permission

home_bp = Blueprint("home", __name__)


@home_bp.get("/home/attention")
@require_permission("supplies.portal.access")
def get_home_attention():
    """operationId: get_supplies_home_attention"""
    service = HomeAttentionService()
    return jsonify(service.compose(g.current_user)), 200
