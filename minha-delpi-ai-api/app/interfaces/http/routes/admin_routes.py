from flask import Blueprint, g, jsonify, request

from app.composition.admin_composer import (
    make_deactivate_knowledge_document_use_case,
    make_get_llm_provider_status_use_case,
    make_list_admin_audit_logs_use_case,
    make_list_admin_knowledge_documents_use_case,
    make_reactivate_knowledge_document_use_case,
)
from app.extensions.db import db
from app.interfaces.http.auth_decorators import require_permission

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/llm/status")
@require_permission("minha-delpi.chat.admin")
def llm_status():
    use_case = make_get_llm_provider_status_use_case()
    return jsonify(use_case.execute()), 200


@admin_bp.get("/knowledge/documents")
@require_permission("minha-delpi.chat.admin")
def list_knowledge_documents():
    limit = request.args.get("limit", 100)
    use_case = make_list_admin_knowledge_documents_use_case()
    return jsonify(use_case.execute(limit=limit)), 200


@admin_bp.post("/knowledge/documents/<document_id>/deactivate")
@require_permission("minha-delpi.chat.admin")
def deactivate_knowledge_document(document_id: str):
    use_case = make_deactivate_knowledge_document_use_case()

    try:
        result = use_case.execute(
            document_id=document_id,
            user_id=g.current_user.sub,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200


@admin_bp.post("/knowledge/documents/<document_id>/reactivate")
@require_permission("minha-delpi.chat.admin")
def reactivate_knowledge_document(document_id: str):
    use_case = make_reactivate_knowledge_document_use_case()

    try:
        result = use_case.execute(
            document_id=document_id,
            user_id=g.current_user.sub,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200


@admin_bp.get("/audit-logs")
@require_permission("minha-delpi.chat.admin")
def list_audit_logs():
    limit = request.args.get("limit", 100)
    use_case = make_list_admin_audit_logs_use_case()
    return jsonify(use_case.execute(limit=limit)), 200
