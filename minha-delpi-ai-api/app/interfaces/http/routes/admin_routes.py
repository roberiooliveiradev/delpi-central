from app.application.security.chat_permissions import (
    CHAT_ACCESS_PERMISSION,
    CHAT_ADMIN_PERMISSION,
    CHAT_ASK_PERMISSION,
    CHAT_HISTORY_VIEW_PERMISSION,
    CHAT_KNOWLEDGE_MANAGE_PERMISSION,
    CHAT_TOOLS_MANAGE_PERMISSION,
    CHAT_TOOLS_USE_PERMISSION,
)
from flask import Blueprint, g, jsonify, request

from app.composition.admin_composer import (
    make_create_external_action_provider_use_case,
    make_import_external_actions_schema_use_case,
    make_list_external_action_providers_use_case,
    make_list_external_actions_use_case,
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








@admin_bp.get("/external-action-providers")
@require_permission(CHAT_ADMIN_PERMISSION)
def list_external_action_providers():
    use_case = make_list_external_action_providers_use_case()
    return jsonify(use_case.execute()), 200


@admin_bp.post("/external-action-providers")
@require_permission(CHAT_ADMIN_PERMISSION)
def create_external_action_provider():
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return jsonify({"errors": [{"code": "invalid_request", "message": "Request body must be a JSON object", "path": "_global"}]}), 400

    use_case = make_create_external_action_provider_use_case()

    try:
        result = use_case.execute(payload)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"errors": [{"code": "external_actions.invalid_input", "message": str(exc), "path": "_global"}]}), 400
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 201


@admin_bp.post("/external-action-providers/<provider_key>/schema")
@require_permission(CHAT_ADMIN_PERMISSION)
def import_external_action_schema(provider_key: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return jsonify({"errors": [{"code": "invalid_request", "message": "Request body must be a JSON object", "path": "_global"}]}), 400

    schema = payload.get("schema")

    use_case = make_import_external_actions_schema_use_case()

    try:
        result = use_case.execute_from_json(provider_key=provider_key, schema_json=schema)

        if not result.get("found"):
            db.session.rollback()
            return jsonify({"errors": [{"code": "not_found", "message": "Provider not found", "path": "_global"}]}), 404

        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"errors": [{"code": "external_actions.invalid_schema", "message": str(exc), "path": "_global"}]}), 400
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200


@admin_bp.post("/external-action-providers/<provider_key>/reload-schema")
@require_permission(CHAT_ADMIN_PERMISSION)
def reload_external_action_schema(provider_key: str):
    use_case = make_import_external_actions_schema_use_case()

    try:
        result = use_case.execute_from_url(provider_key=provider_key)

        if not result.get("found"):
            db.session.rollback()
            return jsonify({"errors": [{"code": "not_found", "message": "Provider not found", "path": "_global"}]}), 404

        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"errors": [{"code": "external_actions.invalid_input", "message": str(exc), "path": "_global"}]}), 400
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200


@admin_bp.get("/external-actions")
@require_permission(CHAT_ADMIN_PERMISSION)
def list_external_actions():
    provider_key = request.args.get("provider")
    use_case = make_list_external_actions_use_case()
    return jsonify(use_case.execute(provider_key=provider_key)), 200


@admin_bp.get("/system-check")
@require_permission(CHAT_ADMIN_PERMISSION)
def admin_system_check():
    use_case = make_get_admin_system_check_use_case()
    return jsonify(use_case.execute()), 200

@admin_bp.get("/metrics/summary")
@require_permission(CHAT_ADMIN_PERMISSION)
def admin_metrics_summary():
    use_case = make_get_admin_metrics_summary_use_case()
    return jsonify(use_case.execute()), 200

@admin_bp.get("/llm/status")
@require_permission(CHAT_ADMIN_PERMISSION)
def llm_status():
    use_case = make_get_llm_provider_status_use_case()
    return jsonify(use_case.execute()), 200


@admin_bp.get("/knowledge/documents")
@require_permission(CHAT_ADMIN_PERMISSION)
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
@require_permission(CHAT_ADMIN_PERMISSION)
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
@require_permission(CHAT_ADMIN_PERMISSION)
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
@require_permission(CHAT_ADMIN_PERMISSION)
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
@require_permission(CHAT_ADMIN_PERMISSION)
def list_audit_logs():
    limit = request.args.get("limit", 100)
    use_case = make_list_admin_audit_logs_use_case()
    return jsonify(use_case.execute(limit=limit)), 200
