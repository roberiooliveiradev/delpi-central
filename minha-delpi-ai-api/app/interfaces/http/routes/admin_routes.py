from flask import Blueprint, g, jsonify, request

from app.composition.admin_composer import (
    make_deactivate_knowledge_document_use_case,
    make_get_llm_provider_status_use_case,
    make_get_admin_metrics_summary_use_case,
    make_get_admin_system_check_use_case,
    make_list_admin_audit_logs_use_case,
    make_list_admin_knowledge_documents_use_case,
    make_reactivate_knowledge_document_use_case,
    make_reindex_knowledge_document_use_case,
)
from app.extensions.db import db
from app.infrastructure.config.settings import Settings
from app.interfaces.http.auth_decorators import require_permission
from app.interfaces.http.rate_limit_decorators import rate_limit

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")






@admin_bp.get("/system-check")
@require_permission("minha-delpi.chat.admin")
def admin_system_check():
    use_case = make_get_admin_system_check_use_case()
    return jsonify(use_case.execute()), 200

@admin_bp.get("/metrics/summary")
@require_permission("minha-delpi.chat.admin")
def admin_metrics_summary():
    use_case = make_get_admin_metrics_summary_use_case()
    return jsonify(use_case.execute()), 200

@admin_bp.get("/llm/status")
@require_permission("minha-delpi.chat.admin")
def llm_status():
    use_case = make_get_llm_provider_status_use_case()
    return jsonify(use_case.execute()), 200


@admin_bp.get("/knowledge/documents")
@require_permission("minha-delpi.chat.admin")
def list_knowledge_documents():
    use_case = make_list_admin_knowledge_documents_use_case()

    return jsonify(
        use_case.execute(
            limit=request.args.get("limit", 20),
            offset=request.args.get("offset", 0),
            search=request.args.get("search"),
            active=request.args.get("active"),
        )
    ), 200


@admin_bp.post("/knowledge/documents/<document_id>/deactivate")
@require_permission("minha-delpi.chat.admin")
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
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
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
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


@admin_bp.post("/knowledge/documents/<document_id>/reindex")
@require_permission("minha-delpi.chat.admin")
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def reindex_knowledge_document(document_id: str):
    use_case = make_reindex_knowledge_document_use_case()

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
