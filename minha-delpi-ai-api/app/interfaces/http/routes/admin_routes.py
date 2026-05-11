from flask import Blueprint, jsonify

from app.composition.admin_composer import make_get_llm_provider_status_use_case
from app.interfaces.http.auth_decorators import require_permission

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/llm/status")
@require_permission("minha-delpi.chat.admin")
def llm_status():
    use_case = make_get_llm_provider_status_use_case()
    return jsonify(use_case.execute()), 200
