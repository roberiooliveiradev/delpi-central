from app.application.security.chat_permissions import (
    CHAT_ACCESS_PERMISSION,
    CHAT_ADMIN_PERMISSION,
    CHAT_ASK_PERMISSION,
    CHAT_HISTORY_VIEW_PERMISSION,
    CHAT_KNOWLEDGE_MANAGE_PERMISSION,
    CHAT_TOOLS_MANAGE_PERMISSION,
    CHAT_TOOLS_USE_PERMISSION,
)
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from flask import Blueprint, Response, g, jsonify, request

from app.application.dto.ingest_document_request import IngestDocumentRequest
from app.domain.exceptions.knowledge_exceptions import InvalidKnowledgeDocumentInputError
from app.application.services.chat_attachment_text_extractor import ChatAttachmentTextExtractor
from app.application.services.knowledge_curatorial_metadata_service import (
    build_global_curatorial_metadata,
    merge_curatorial_metadata,
)
from app.composition.admin_composer import (
    make_archive_admin_guideline_use_case,
    make_compare_admin_guideline_versions_use_case,
    make_create_external_action_provider_use_case,
    make_import_external_actions_schema_use_case,
    make_list_external_action_providers_use_case,
    make_list_external_actions_use_case,
    make_deactivate_knowledge_document_use_case,
    make_delete_knowledge_document_use_case,
    make_ingest_admin_knowledge_document_use_case,
    make_get_llm_provider_status_use_case,
    make_get_admin_drawing_analysis_summary_use_case,
    make_get_admin_document_vision_summary_use_case,
    make_get_admin_intent_routing_summary_use_case,
    make_get_admin_text_task_summary_use_case,
    make_get_admin_metrics_summary_use_case,
    make_get_admin_chat_intelligence_settings_use_case,
    make_get_admin_llm_cost_table_use_case,
    make_reindex_external_action_embeddings_use_case,
    make_save_admin_chat_intelligence_settings_use_case,
    make_save_admin_llm_cost_table_use_case,
    make_get_admin_tools_health_use_case,
    make_get_admin_rbac_summary_use_case,
    make_get_admin_rbac_profiles_use_case,
    make_get_admin_system_check_use_case,
    make_list_admin_audit_logs_use_case,
    make_list_admin_guidelines_use_case,
    make_list_admin_guideline_versions_use_case,
    make_list_admin_knowledge_documents_use_case,
    make_preview_knowledge_ingestion_use_case,
    make_update_admin_knowledge_document_metadata_use_case,
    make_reactivate_knowledge_document_use_case,
    make_publish_admin_guideline_use_case,
    make_reindex_knowledge_document_use_case,
    make_restore_admin_guideline_version_use_case,
    make_save_admin_guideline_use_case,
    make_list_admin_chat_skills_use_case,
    make_create_admin_chat_skill_use_case,
    make_update_admin_chat_skill_use_case,
    make_deactivate_admin_chat_skill_use_case,
    make_admin_agent_simulate_use_case,
    make_get_admin_response_evaluation_context_use_case,
    make_get_admin_agent_specialization_use_case,
    make_get_admin_response_evaluation_summary_use_case,
    make_list_admin_agent_specialization_presets_use_case,
    make_list_admin_specialized_agents_use_case,
    make_save_admin_agent_specialization_use_case,
    make_list_admin_response_candidates_use_case,
    make_list_admin_response_evaluations_use_case,
    make_save_admin_response_evaluation_use_case,
    make_get_admin_security_config_use_case,
    make_get_admin_security_summary_use_case,
    make_list_admin_security_events_use_case,
    make_scan_admin_security_input_use_case,
    make_test_admin_rag_use_case,
)
from app.extensions.db import db
from app.infrastructure.config.settings import Settings
from app.infrastructure.persistence.postgres_audit_repository import PostgresAuditRepository
from app.infrastructure.gateways.core_api_http_gateway import CoreApiHttpGateway
from app.interfaces.http.auth_decorators import require_permission
from app.interfaces.http.rate_limit_decorators import rate_limit

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")












@admin_bp.get("/rbac/summary")
@require_permission(CHAT_ACCESS_PERMISSION)
def get_admin_rbac_summary():
    authorization_header = request.headers.get("Authorization") or ""
    access_token = authorization_header.removeprefix("Bearer ").strip()
    core_user = CoreApiHttpGateway().get_me(access_token)

    use_case = make_get_admin_rbac_summary_use_case()
    return jsonify(use_case.execute(g.current_user, core_user=core_user)), 200


@admin_bp.get("/rbac/profiles")
@require_permission(CHAT_ACCESS_PERMISSION)
def get_admin_rbac_profiles():
    use_case = make_get_admin_rbac_profiles_use_case()
    return jsonify(use_case.execute()), 200


@admin_bp.get("/skills")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def list_admin_chat_skills():
    include_inactive = request.args.get("includeInactive", "true").lower() != "false"
    use_case = make_list_admin_chat_skills_use_case()
    return jsonify(use_case.execute(include_inactive=include_inactive)), 200


@admin_bp.post("/skills")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def create_admin_chat_skill():
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return jsonify({"errors": [{"code": "invalid_request", "message": "Request body must be a JSON object", "path": "_global"}]}), 400

    use_case = make_create_admin_chat_skill_use_case()

    try:
        result = use_case.execute(payload)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"errors": [{"code": "invalid_request", "message": str(exc), "path": "_global"}]}), 400
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 201


@admin_bp.put("/skills/<skill_id>")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def update_admin_chat_skill(skill_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return jsonify({"errors": [{"code": "invalid_request", "message": "Request body must be a JSON object", "path": "_global"}]}), 400

    use_case = make_update_admin_chat_skill_use_case()

    try:
        result = use_case.execute(skill_id, payload)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"errors": [{"code": "invalid_request", "message": str(exc), "path": "_global"}]}), 400
    except Exception:
        db.session.rollback()
        raise

    if not result:
        return jsonify({"errors": [{"code": "not_found", "message": "Skill not found", "path": "skillId"}]}), 404

    return jsonify(result), 200


@admin_bp.delete("/skills/<skill_id>")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def deactivate_admin_chat_skill(skill_id: str):
    use_case = make_deactivate_admin_chat_skill_use_case()

    try:
        deleted = use_case.execute(skill_id)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    if not deleted:
        return jsonify({"errors": [{"code": "not_found", "message": "Skill not found", "path": "skillId"}]}), 404

    return jsonify({"ok": True}), 200


@admin_bp.get("/guidelines")
@require_permission(CHAT_ADMIN_PERMISSION)
def list_admin_guidelines():
    use_case = make_list_admin_guidelines_use_case()
    return jsonify(use_case.execute()), 200






@admin_bp.get("/guidelines/<guideline_id>/versions/compare")
@require_permission(CHAT_ADMIN_PERMISSION)
def compare_admin_guideline_versions(guideline_id: str):
    from_version = request.args.get("fromVersion")
    to_version = request.args.get("toVersion")

    if not from_version or not to_version:
        return jsonify({"errors": [{"code": "invalid_request", "message": "fromVersion and toVersion are required", "path": "_global"}]}), 400

    use_case = make_compare_admin_guideline_versions_use_case()

    try:
        result = use_case.execute(
            guideline_id,
            from_version=int(from_version),
            to_version=int(to_version),
        )
    except ValueError as exc:
        return jsonify({"errors": [{"code": "invalid_request", "message": str(exc), "path": "_global"}]}), 400

    return jsonify(result), 200


@admin_bp.post("/guidelines/<guideline_id>/versions/<int:version>/restore")
@require_permission(CHAT_ADMIN_PERMISSION)
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def restore_admin_guideline_version(guideline_id: str, version: int):
    use_case = make_restore_admin_guideline_version_use_case()

    try:
        result = use_case.execute(
            guideline_id,
            version=version,
            user_id=g.current_user.sub,
        )
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"errors": [{"code": "invalid_request", "message": str(exc), "path": "_global"}]}), 400
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200


@admin_bp.get("/guidelines/<guideline_id>/versions")
@require_permission(CHAT_ADMIN_PERMISSION)
def list_admin_guideline_versions(guideline_id: str):
    use_case = make_list_admin_guideline_versions_use_case()
    return jsonify(use_case.execute(guideline_id)), 200


@admin_bp.post("/guidelines")
@require_permission(CHAT_ADMIN_PERMISSION)
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def save_admin_guideline():
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return jsonify({"errors": [{"code": "invalid_request", "message": "Request body must be a JSON object", "path": "_global"}]}), 400

    use_case = make_save_admin_guideline_use_case()

    try:
        result = use_case.execute(payload, user_id=g.current_user.sub)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"errors": [{"code": "invalid_request", "message": str(exc), "path": "_global"}]}), 400
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 201


@admin_bp.post("/guidelines/<guideline_id>/publish")
@require_permission(CHAT_ADMIN_PERMISSION)
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def publish_admin_guideline(guideline_id: str):
    use_case = make_publish_admin_guideline_use_case()

    try:
        result = use_case.execute(guideline_id, user_id=g.current_user.sub)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"errors": [{"code": "not_found", "message": str(exc), "path": "guidelineId"}]}), 404
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200


@admin_bp.post("/guidelines/<guideline_id>/archive")
@require_permission(CHAT_ADMIN_PERMISSION)
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def archive_admin_guideline(guideline_id: str):
    use_case = make_archive_admin_guideline_use_case()

    try:
        result = use_case.execute(guideline_id, user_id=g.current_user.sub)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"errors": [{"code": "not_found", "message": str(exc), "path": "guidelineId"}]}), 404
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200


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


@admin_bp.post("/rag/test")
@require_permission(CHAT_ADMIN_PERMISSION)
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def test_admin_rag():
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return jsonify({"errors": [{"code": "invalid_request", "message": "Request body must be a JSON object", "path": "_global"}]}), 400

    use_case = make_test_admin_rag_use_case()

    try:
        result = use_case.execute(
            question=payload.get("question"),
            document_id=payload.get("documentId"),
            limit=payload.get("limit", 5),
        )
    except ValueError as exc:
        return jsonify({"errors": [{"code": "invalid_request", "message": str(exc), "path": "question"}]}), 400

    score = float(result.get("score") or 0)
    chunks = result.get("chunks") or []
    assertive = score >= Settings.RAG_ASSERTIVENESS_MIN_SCORE and len(chunks) > 0

    try:
        PostgresAuditRepository().log(
            user_id=UUID(str(g.current_user.sub)),
            action="admin.rag.tested",
            context="admin",
            metadata={
                "score": score,
                "chunk_count": len(chunks),
                "document_count": len(result.get("matchedDocuments") or []),
                "assertive": assertive,
                "question_preview": str(result.get("question") or "")[:200],
            },
        )
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify(result), 200


@admin_bp.post("/agent/simulate")
@require_permission(CHAT_ADMIN_PERMISSION)
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def simulate_admin_agent():
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return jsonify(
            {"errors": [{"code": "invalid_request", "message": "Request body must be a JSON object", "path": "_global"}]},
        ), 400

    generate_answer = bool(payload.get("generateAnswer"))

    use_case = make_admin_agent_simulate_use_case(with_llm=generate_answer)

    try:
        result = use_case.execute(
            question=payload.get("question"),
            agent_id=payload.get("agentId"),
            document_id=payload.get("documentId"),
            session_id=payload.get("sessionId"),
            generate_answer=generate_answer,
            execute_tools_in_sandbox=bool(payload.get("executeToolsInSandbox")),
            user_id=str(g.current_user.sub),
            access_token=getattr(g, "access_token", None),
        )
    except ValueError as exc:
        return jsonify(
            {"errors": [{"code": "invalid_request", "message": str(exc), "path": "question"}]},
        ), 400

    try:
        PostgresAuditRepository().log(
            user_id=UUID(str(g.current_user.sub)),
            action="admin.agent.simulated",
            context="admin",
            metadata={
                "generate_answer": generate_answer,
                "agent_id": payload.get("agentId"),
                "guideline_count": len(result.get("appliedGuidelines") or []),
                "chunk_count": len(result.get("chunks") or []),
                "planned_tool_count": len(result.get("plannedToolCalls") or []),
                "question_preview": str(result.get("question") or "")[:200],
            },
        )
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify(result), 200


@admin_bp.get("/system-check")
@require_permission(CHAT_ADMIN_PERMISSION)
def admin_system_check():
    use_case = make_get_admin_system_check_use_case()
    return jsonify(use_case.execute()), 200

@admin_bp.get("/metrics/summary")
@require_permission(CHAT_ADMIN_PERMISSION)
def admin_metrics_summary():
    use_case = make_get_admin_metrics_summary_use_case()
    hours_raw = request.args.get("hours", 24)

    try:
        hours = int(hours_raw)
    except (TypeError, ValueError):
        return jsonify(
            {"errors": [{"code": "invalid_request", "message": "hours must be an integer", "path": "hours"}]},
        ), 400

    return jsonify(use_case.execute(hours=hours)), 200


@admin_bp.get("/metrics/drawing-analysis/summary")
@require_permission(CHAT_ADMIN_PERMISSION)
def admin_drawing_analysis_metrics_summary():
    use_case = make_get_admin_drawing_analysis_summary_use_case()
    hours_raw = request.args.get("hours", 168)

    try:
        hours = int(hours_raw)
    except (TypeError, ValueError):
        return jsonify(
            {
                "errors": [
                    {
                        "code": "invalid_request",
                        "message": "hours must be an integer",
                        "path": "hours",
                    }
                ]
            },
        ), 400

    return jsonify(use_case.execute(hours=hours)), 200


@admin_bp.get("/metrics/intent-routing/summary")
@require_permission(CHAT_ADMIN_PERMISSION)
def admin_intent_routing_metrics_summary():
    use_case = make_get_admin_intent_routing_summary_use_case()
    hours_raw = request.args.get("hours", 168)

    try:
        hours = int(hours_raw)
    except (TypeError, ValueError):
        return jsonify(
            {
                "errors": [
                    {
                        "code": "invalid_request",
                        "message": "hours must be an integer",
                        "path": "hours",
                    }
                ]
            },
        ), 400

    return jsonify(use_case.execute(hours=hours)), 200


@admin_bp.get("/metrics/text-tasks/summary")
@require_permission(CHAT_ADMIN_PERMISSION)
def admin_text_task_metrics_summary():
    use_case = make_get_admin_text_task_summary_use_case()
    hours_raw = request.args.get("hours", 168)

    try:
        hours = int(hours_raw)
    except (TypeError, ValueError):
        return jsonify(
            {
                "errors": [
                    {
                        "code": "invalid_request",
                        "message": "hours must be an integer",
                        "path": "hours",
                    }
                ]
            },
        ), 400

    return jsonify(use_case.execute(hours=hours)), 200


@admin_bp.get("/metrics/document-vision/summary")
@require_permission(CHAT_ADMIN_PERMISSION)
def admin_document_vision_metrics_summary():
    use_case = make_get_admin_document_vision_summary_use_case()
    hours_raw = request.args.get("hours", 168)

    try:
        hours = int(hours_raw)
    except (TypeError, ValueError):
        return jsonify(
            {
                "errors": [
                    {
                        "code": "invalid_request",
                        "message": "hours must be an integer",
                        "path": "hours",
                    }
                ]
            },
        ), 400

    return jsonify(use_case.execute(hours=hours)), 200


@admin_bp.get("/metrics/timeseries")
@require_permission(CHAT_ADMIN_PERMISSION)
def admin_metrics_timeseries():
    use_case = make_get_admin_metrics_summary_use_case()
    hours_raw = request.args.get("hours", 168)
    bucket_raw = request.args.get("bucketHours", 24)

    try:
        hours = int(hours_raw)
        bucket_hours = int(bucket_raw)
    except (TypeError, ValueError):
        return jsonify(
            {
                "errors": [
                    {
                        "code": "invalid_request",
                        "message": "hours and bucketHours must be integers",
                        "path": "_global",
                    }
                ]
            },
        ), 400

    return jsonify(use_case.execute_timeseries(hours=hours, bucket_hours=bucket_hours)), 200


@admin_bp.get("/metrics/cost-table")
@require_permission(CHAT_ADMIN_PERMISSION)
def get_admin_llm_cost_table():
    use_case = make_get_admin_llm_cost_table_use_case()
    return jsonify(use_case.execute()), 200


@admin_bp.put("/metrics/cost-table")
@require_permission(CHAT_ADMIN_PERMISSION)
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def save_admin_llm_cost_table():
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return jsonify(
            {"errors": [{"code": "invalid_request", "message": "Request body must be a JSON object", "path": "_global"}]},
        ), 400

    use_case = make_save_admin_llm_cost_table_use_case()

    try:
        result = use_case.execute(entries=payload.get("entries") or [])
    except ValueError as exc:
        return jsonify(
            {"errors": [{"code": "invalid_request", "message": str(exc), "path": "entries"}]},
        ), 400

    try:
        PostgresAuditRepository().log(
            user_id=UUID(str(g.current_user.sub)),
            action="admin.metrics.cost_table.updated",
            context="admin",
            metadata={"entryCount": len(result.get("entries") or [])},
        )
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify(result), 200


@admin_bp.get("/chat/intelligence-settings")
@require_permission(CHAT_ADMIN_PERMISSION)
def get_admin_chat_intelligence_settings():
    use_case = make_get_admin_chat_intelligence_settings_use_case()
    return jsonify(use_case.execute()), 200


@admin_bp.put("/chat/intelligence-settings")
@require_permission(CHAT_ADMIN_PERMISSION)
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def save_admin_chat_intelligence_settings():
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return jsonify(
            {"errors": [{"code": "invalid_request", "message": "Request body must be a JSON object", "path": "_global"}]},
        ), 400

    use_case = make_save_admin_chat_intelligence_settings_use_case()

    try:
        result = use_case.execute(payload)
    except ValueError as exc:
        return jsonify(
            {"errors": [{"code": "invalid_request", "message": str(exc), "path": "_global"}]},
        ), 400

    try:
        PostgresAuditRepository().log(
            user_id=UUID(str(g.current_user.sub)),
            action="admin.chat.intelligence_settings.updated",
            context="admin",
            metadata={"keys": list(payload.keys())},
        )
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify(result), 200


@admin_bp.post("/tools/actions/reindex-embeddings")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def reindex_external_action_embeddings():
    payload = request.get_json(silent=True) or {}
    provider_key = payload.get("providerKey") if isinstance(payload, dict) else None

    use_case = make_reindex_external_action_embeddings_use_case()
    result = use_case.execute(provider_key=str(provider_key).strip() if provider_key else None)

    try:
        PostgresAuditRepository().log(
            user_id=UUID(str(g.current_user.sub)),
            action="admin.tools.actions.reindex_embeddings",
            context="admin",
            metadata=result,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify(result), 200


@admin_bp.get("/tools/health")
@require_permission(CHAT_ADMIN_PERMISSION)
def admin_tools_health():
    authorization_header = request.headers.get("Authorization") or ""
    access_token = authorization_header.removeprefix("Bearer ").strip() or None
    use_case = make_get_admin_tools_health_use_case()
    return jsonify(use_case.execute(access_token=access_token)), 200

@admin_bp.get("/llm/status")
@require_permission(CHAT_ADMIN_PERMISSION)
def llm_status():
    use_case = make_get_llm_provider_status_use_case()
    return jsonify(use_case.execute()), 200


@admin_bp.post("/knowledge/ingest/preview")
@require_permission(CHAT_ADMIN_PERMISSION)
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def preview_knowledge_ingestion():
    use_case = make_preview_knowledge_ingestion_use_case()
    extractor = ChatAttachmentTextExtractor()

    if request.files.get("file"):
        uploaded_file = request.files["file"]

        if not uploaded_file.filename:
            return jsonify(
                {"errors": [{"code": "invalid_request", "message": "file is required", "path": "file"}]},
            ), 400

        raw_bytes = uploaded_file.read()

        if not raw_bytes:
            return jsonify(
                {"errors": [{"code": "invalid_request", "message": "empty files cannot be previewed", "path": "file"}]},
            ), 400

        original_filename = Path(uploaded_file.filename).name
        suffix = Path(original_filename).suffix

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(raw_bytes)
            tmp_path = tmp.name

        try:
            extracted = extractor.extract(
                storage_path=tmp_path,
                filename=original_filename,
                content_type=uploaded_file.content_type,
            )
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        if not extracted.get("supported"):
            return jsonify(
                {
                    "errors": [
                        {
                            "code": "knowledge.unsupported_file",
                            "message": "file type is not supported for preview",
                            "path": "file",
                        }
                    ]
                },
            ), 400

        content = str(extracted.get("content") or "").strip()

        if not content:
            return jsonify(
                {
                    "errors": [
                        {
                            "code": "knowledge.empty_extracted_content",
                            "message": "file did not produce indexable text",
                            "path": "file",
                        }
                    ]
                },
            ), 400

        title = (request.form.get("title") or original_filename).strip()
        source_type = (request.form.get("sourceType") or "admin_preview_upload").strip()
        source_ref = (request.form.get("sourceRef") or f"preview:{Path(uploaded_file.filename).name}").strip()
        metadata = {"origin": "admin_preview_upload", "originalFilename": Path(uploaded_file.filename).name}
        check_semantic = request.form.get("checkSemanticDuplicates", "true").lower() != "false"
    else:
        payload = request.get_json(silent=True) or {}

        if not isinstance(payload, dict):
            return jsonify(
                {"errors": [{"code": "invalid_request", "message": "Request body must be a JSON object", "path": "_global"}]},
            ), 400

        content = payload.get("content", "")
        title = payload.get("title")
        source_type = payload.get("sourceType")
        source_ref = payload.get("sourceRef")
        metadata = payload.get("metadata")
        check_semantic = payload.get("checkSemanticDuplicates", True) is not False

    try:
        result = use_case.execute(
            content=content,
            title=title,
            source_type=source_type,
            source_ref=source_ref,
            metadata=metadata,
            check_semantic_duplicates=bool(check_semantic),
        )
    except InvalidKnowledgeDocumentInputError as exc:
        return jsonify(
            {"errors": [{"code": "invalid_request", "message": str(exc), "path": "content"}]},
        ), 400

    return jsonify(result), 200


@admin_bp.post("/knowledge/documents/upload")
@require_permission(CHAT_ADMIN_PERMISSION)
@rate_limit("knowledge_writes", Settings.RATE_LIMIT_KNOWLEDGE_WRITES_PER_WINDOW)
def upload_knowledge_document():
    uploaded_file = request.files.get("file")

    if not uploaded_file or not uploaded_file.filename:
        return jsonify({"errors": [{"code": "invalid_request", "message": "file is required", "path": "file"}]}), 400

    raw_bytes = uploaded_file.read()

    if not raw_bytes:
        return jsonify({"errors": [{"code": "invalid_request", "message": "empty files cannot be ingested", "path": "file"}]}), 400

    original_filename = Path(uploaded_file.filename).name
    title = (request.form.get("title") or original_filename).strip()
    source_type = (request.form.get("sourceType") or "admin_upload").strip()
    source_ref = (request.form.get("sourceRef") or f"admin_upload:{original_filename}").strip()

    metadata = build_global_curatorial_metadata(
        category=request.form.get("category"),
        tags=request.form.get("tags"),
        namespace=request.form.get("namespace"),
        domain=request.form.get("domain"),
        priority=request.form.get("priority"),
        quality_score=request.form.get("qualityScore"),
        extra={
            "origin": "admin_upload",
            "originalFilename": original_filename,
            "contentType": uploaded_file.content_type,
            "sizeBytes": len(raw_bytes),
        },
    )

    metadata_raw = request.form.get("metadata")
    if metadata_raw:
        try:
            extra_metadata = json.loads(metadata_raw)
            if isinstance(extra_metadata, dict):
                metadata = merge_curatorial_metadata(
                    metadata,
                    category=extra_metadata.get("category"),
                    tags=extra_metadata.get("tags"),
                    namespace=extra_metadata.get("namespace"),
                    domain=extra_metadata.get("domain"),
                    priority=extra_metadata.get("priority"),
                    quality_score=extra_metadata.get("qualityScore"),
                )
                metadata.update(
                    {
                        key: value
                        for key, value in extra_metadata.items()
                        if key
                        not in {
                            "category",
                            "tags",
                            "namespace",
                            "domain",
                            "priority",
                            "qualityScore",
                        }
                    }
                )
        except json.JSONDecodeError:
            return jsonify({"errors": [{"code": "invalid_request", "message": "metadata must be valid JSON", "path": "metadata"}]}), 400

    suffix = Path(original_filename).suffix

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(raw_bytes)
        tmp_path = tmp.name

    try:
        extracted = ChatAttachmentTextExtractor().extract(
            storage_path=tmp_path,
            filename=original_filename,
            content_type=uploaded_file.content_type,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    metadata["extractor"] = extracted.get("metadata")

    if not extracted.get("supported"):
        return jsonify({"errors": [{"code": "knowledge.unsupported_file", "message": "file type is not supported for knowledge ingestion", "path": "file", "metadata": extracted.get("metadata")}]}), 400

    content = str(extracted.get("content") or "").strip()

    if not content:
        return jsonify({"errors": [{"code": "knowledge.empty_extracted_content", "message": "file did not produce indexable text", "path": "file", "metadata": extracted.get("metadata")}]}), 400

    use_case = make_ingest_admin_knowledge_document_use_case()

    try:
        result = use_case.execute(
            IngestDocumentRequest(
                title=title,
                source_type=source_type,
                source_ref=source_ref,
                content=content,
                metadata=metadata,
                user_id=g.current_user.sub,
            )
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 201


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
            category=request.args.get("category"),
            namespace=request.args.get("namespace"),
            domain=request.args.get("domain"),
            tag=request.args.get("tag"),
            source_type=request.args.get("sourceType"),
        )
    ), 200


@admin_bp.patch("/knowledge/documents/<document_id>/metadata")
@require_permission(CHAT_ADMIN_PERMISSION)
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def update_knowledge_document_metadata(document_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return jsonify(
            {"errors": [{"code": "invalid_request", "message": "Request body must be a JSON object", "path": "_global"}]},
        ), 400

    use_case = make_update_admin_knowledge_document_metadata_use_case()

    try:
        result = use_case.execute(
            document_id=document_id,
            category=payload.get("category"),
            tags=payload.get("tags"),
            namespace=payload.get("namespace"),
            domain=payload.get("domain"),
            priority=payload.get("priority"),
            quality_score=payload.get("qualityScore"),
        )
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"errors": [{"code": "not_found", "message": str(exc), "path": "documentId"}]}), 404
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200


@admin_bp.delete("/knowledge/documents/<document_id>")
@require_permission(CHAT_ADMIN_PERMISSION)
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def delete_knowledge_document(document_id: str):
    use_case = make_delete_knowledge_document_use_case()

    try:
        result = use_case.execute(
            document_id=document_id,
            user_id=g.current_user.sub,
        )
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"errors": [{"code": "not_found", "message": str(exc), "path": "documentId"}]}), 404
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200


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


@admin_bp.get("/agents/specializations/catalog")
@require_permission(CHAT_ADMIN_PERMISSION)
def list_agent_specialization_presets():
    use_case = make_list_admin_agent_specialization_presets_use_case()
    return jsonify(use_case.execute()), 200


@admin_bp.get("/agents/specialized")
@require_permission(CHAT_ADMIN_PERMISSION)
def list_specialized_agents():
    use_case = make_list_admin_specialized_agents_use_case()
    return jsonify(use_case.execute()), 200


@admin_bp.get("/agents/<agent_id>/specialization")
@require_permission(CHAT_ADMIN_PERMISSION)
def get_agent_specialization(agent_id: str):
    use_case = make_get_admin_agent_specialization_use_case()

    try:
        result = use_case.execute(agent_id=agent_id)
    except ValueError as exc:
        return jsonify(
            {"errors": [{"code": "not_found", "message": str(exc), "path": "agentId"}]},
        ), 404

    return jsonify(result), 200


@admin_bp.put("/agents/<agent_id>/specialization")
@require_permission(CHAT_ADMIN_PERMISSION)
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def save_agent_specialization(agent_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return jsonify(
            {"errors": [{"code": "invalid_request", "message": "Request body must be a JSON object", "path": "_global"}]},
        ), 400

    use_case = make_save_admin_agent_specialization_use_case()

    try:
        result = use_case.execute(
            agent_id=agent_id,
            specialization_payload=payload.get("specialization"),
            user_id=str(g.current_user.sub),
        )
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify(
            {"errors": [{"code": "invalid_request", "message": str(exc), "path": "specialization"}]},
        ), 400
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200


@admin_bp.get("/responses/evaluations/summary")
@require_permission(CHAT_ADMIN_PERMISSION)
def response_evaluations_summary():
    use_case = make_get_admin_response_evaluation_summary_use_case()
    return jsonify(use_case.execute()), 200


@admin_bp.get("/responses/candidates")
@require_permission(CHAT_ADMIN_PERMISSION)
def list_response_candidates():
    use_case = make_list_admin_response_candidates_use_case()

    return jsonify(
        use_case.execute(
            limit=request.args.get("limit", 20),
            offset=request.args.get("offset", 0),
            search=request.args.get("search"),
        )
    ), 200


@admin_bp.get("/responses/messages/<message_id>/evaluation-context")
@require_permission(CHAT_ADMIN_PERMISSION)
def get_response_evaluation_context(message_id: str):
    use_case = make_get_admin_response_evaluation_context_use_case()
    score_raw = request.args.get("score")

    try:
        score = int(score_raw) if score_raw is not None else None
        use_llm = request.args.get("useLlmSuggestions", "false").lower() in {"1", "true", "yes"}
        result = use_case.execute(
            message_id=message_id,
            score=score,
            use_llm_suggestions=use_llm,
        )
    except ValueError as exc:
        return jsonify(
            {"errors": [{"code": "not_found", "message": str(exc), "path": "messageId"}]},
        ), 404

    return jsonify(result), 200


@admin_bp.get("/responses/evaluations")
@require_permission(CHAT_ADMIN_PERMISSION)
def list_response_evaluations():
    use_case = make_list_admin_response_evaluations_use_case()

    min_score = request.args.get("minScore")
    max_score = request.args.get("maxScore")

    return jsonify(
        use_case.execute(
            limit=request.args.get("limit", 20),
            offset=request.args.get("offset", 0),
            verdict=request.args.get("verdict"),
            min_score=int(min_score) if min_score is not None else None,
            max_score=int(max_score) if max_score is not None else None,
            search=request.args.get("search"),
        )
    ), 200


@admin_bp.post("/responses/evaluations")
@require_permission(CHAT_ADMIN_PERMISSION)
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def save_response_evaluation():
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return jsonify(
            {"errors": [{"code": "invalid_request", "message": "Request body must be a JSON object", "path": "_global"}]},
        ), 400

    use_case = make_save_admin_response_evaluation_use_case()

    try:
        result = use_case.execute(
            message_id=payload.get("messageId"),
            evaluator_user_id=str(g.current_user.sub),
            score=payload.get("score", 3),
            comment=payload.get("comment"),
        )
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify(
            {"errors": [{"code": "not_found", "message": str(exc), "path": "messageId"}]},
        ), 404
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200


@admin_bp.get("/security/config")
@require_permission(CHAT_ADMIN_PERMISSION)
def get_admin_security_config():
    use_case = make_get_admin_security_config_use_case()
    return jsonify(use_case.execute()), 200


@admin_bp.get("/security/summary")
@require_permission(CHAT_ADMIN_PERMISSION)
def get_admin_security_summary():
    use_case = make_get_admin_security_summary_use_case()

    try:
        hours = int(request.args.get("hours", 24))
    except ValueError:
        hours = 24

    return jsonify(use_case.execute(hours=hours)), 200


@admin_bp.get("/security/events")
@require_permission(CHAT_ADMIN_PERMISSION)
def list_admin_security_events():
    use_case = make_list_admin_security_events_use_case()

    try:
        result = use_case.execute(
            limit=request.args.get("limit", 50),
            offset=request.args.get("offset", 0),
            action=request.args.get("action"),
            user_id=request.args.get("userId"),
            date_from=request.args.get("dateFrom"),
            date_to=request.args.get("dateTo"),
        )
    except ValueError as exc:
        return jsonify(
            {"errors": [{"code": "invalid_request", "message": str(exc), "path": "_global"}]},
        ), 400

    return jsonify(result), 200


@admin_bp.post("/security/scan")
@require_permission(CHAT_ADMIN_PERMISSION)
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def scan_admin_security_input():
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return jsonify(
            {"errors": [{"code": "invalid_request", "message": "Invalid JSON body", "path": "_global"}]},
        ), 400

    message = payload.get("message")

    if not isinstance(message, str) or not message.strip():
        return jsonify(
            {"errors": [{"code": "invalid_request", "message": "message is required", "path": "message"}]},
        ), 400

    use_case = make_scan_admin_security_input_use_case()

    parsed_user_id = None

    if getattr(g, "current_user", None) and getattr(g.current_user, "sub", None):
        parsed_user_id = UUID(str(g.current_user.sub))

    try:
        result = use_case.execute(
            message=message,
            user_id=parsed_user_id,
            context=payload.get("context"),
        )
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify(
            {"errors": [{"code": "invalid_request", "message": str(exc), "path": "_global"}]},
        ), 400
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200


@admin_bp.get("/audit-logs")
@require_permission(CHAT_ADMIN_PERMISSION)
def list_audit_logs():
    use_case = make_list_admin_audit_logs_use_case()

    try:
        result = use_case.execute(
            limit=request.args.get("limit", 50),
            offset=request.args.get("offset", 0),
            action=request.args.get("action"),
            context=request.args.get("context"),
            user_id=request.args.get("userId"),
            trace_id=request.args.get("traceId"),
            search=request.args.get("search"),
            date_from=request.args.get("dateFrom"),
            date_to=request.args.get("dateTo"),
        )
    except ValueError as exc:
        return jsonify(
            {"errors": [{"code": "invalid_request", "message": str(exc), "path": "_global"}]},
        ), 400

    return jsonify(result), 200


@admin_bp.get("/audit-logs/timeline")
@require_permission(CHAT_ADMIN_PERMISSION)
def audit_logs_timeline():
    use_case = make_list_admin_audit_logs_use_case()

    try:
        max_days = request.args.get("maxDays")
        result = use_case.execute_timeline(
            action=request.args.get("action"),
            context=request.args.get("context"),
            user_id=request.args.get("userId"),
            trace_id=request.args.get("traceId"),
            search=request.args.get("search"),
            date_from=request.args.get("dateFrom"),
            date_to=request.args.get("dateTo"),
            max_days=int(max_days) if max_days is not None else None,
        )
    except ValueError as exc:
        return jsonify(
            {"errors": [{"code": "invalid_request", "message": str(exc), "path": "_global"}]},
        ), 400

    return jsonify(result), 200


@admin_bp.get("/audit-logs/export")
@require_permission(CHAT_ADMIN_PERMISSION)
@rate_limit("admin_actions", Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)
def export_audit_logs():
    use_case = make_list_admin_audit_logs_use_case()
    export_format = (request.args.get("format") or "json").lower().strip()

    try:
        if export_format == "csv":
            csv_content = use_case.execute_export_csv(
                action=request.args.get("action"),
                context=request.args.get("context"),
                user_id=request.args.get("userId"),
                trace_id=request.args.get("traceId"),
                search=request.args.get("search"),
                date_from=request.args.get("dateFrom"),
                date_to=request.args.get("dateTo"),
            )
        else:
            result = use_case.execute_export(
                action=request.args.get("action"),
                context=request.args.get("context"),
                user_id=request.args.get("userId"),
                trace_id=request.args.get("traceId"),
                search=request.args.get("search"),
                date_from=request.args.get("dateFrom"),
                date_to=request.args.get("dateTo"),
            )
    except ValueError as exc:
        return jsonify(
            {"errors": [{"code": "invalid_request", "message": str(exc), "path": "_global"}]},
        ), 400

    if export_format == "csv":
        filename = f"minha-delpi-audit-{datetime.now(timezone.utc).date().isoformat()}.csv"
        return Response(
            csv_content,
            mimetype="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    return jsonify(result), 200


@admin_bp.get("/audit-logs/<int:log_id>")
@require_permission(CHAT_ADMIN_PERMISSION)
def get_audit_log_detail(log_id: int):
    use_case = make_list_admin_audit_logs_use_case()
    result = use_case.execute_detail(log_id)

    if not result:
        return jsonify(
            {"errors": [{"code": "not_found", "message": "Log não encontrado.", "path": "logId"}]},
        ), 404

    return jsonify(result), 200
