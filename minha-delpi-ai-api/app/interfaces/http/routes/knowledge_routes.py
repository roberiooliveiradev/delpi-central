from flask import Blueprint, g, jsonify, request

from app.application.dto.ingest_document_request import IngestDocumentRequest
from app.application.dto.search_knowledge_request import SearchKnowledgeRequest
from app.composition.knowledge_composer import (
    make_ingest_knowledge_document_use_case,
    make_search_knowledge_use_case,
)
from app.extensions.db import db
from app.infrastructure.config.settings import Settings
from app.interfaces.http.auth_decorators import require_permission
from app.interfaces.http.rate_limit_decorators import rate_limit
from app.interfaces.http.utils.errors import bad_request

knowledge_bp = Blueprint("knowledge", __name__, url_prefix="/knowledge")


@knowledge_bp.post("/documents")
@require_permission("minha-delpi.chat.knowledge.manage")
@rate_limit("knowledge_writes", Settings.RATE_LIMIT_KNOWLEDGE_WRITES_PER_WINDOW)
def ingest_document():
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_ingest_knowledge_document_use_case()

    try:
        result = use_case.execute(
            IngestDocumentRequest(
                title=payload.get("title", ""),
                source_type=payload.get("sourceType", "manual"),
                source_ref=payload.get("sourceRef"),
                content=payload.get("content", ""),
                metadata=payload.get("metadata"),
                user_id=g.current_user.sub,
            )
        )

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 201


@knowledge_bp.post("/search")
@require_permission("minha-delpi.chat.access")
def search_knowledge():
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_search_knowledge_use_case()

    result = use_case.execute(
        SearchKnowledgeRequest(
            query=payload.get("query", ""),
            limit=int(payload.get("limit", 6)),
        )
    )

    return jsonify(result), 200
