from __future__ import annotations

import logging
import re

from fastapi import APIRouter, Path, Query
from delpi_auth.authorization import require_any_permission

from app.application.dto.governed_knowledge_response import GovernedKnowledgeEnvelope
from app.application.security.api_delpi_permissions import API_DELPI_ACCESS
from app.application.use_cases.read_governed_technical_knowledge_use_case import KnowledgeReadError
from scripts.davi_governed_knowledge_bundle_lib import LATEST_CORPUS_VERSION
from app.composition.governed_knowledge_composer import (
    build_read_governed_technical_knowledge,
    published_knowledge_topics,
)
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata import GOVERNED_TECHNICAL_KNOWLEDGE
from app.interface.http.pagination_query import PAGE_SIZE_QUERY
from app.interface.http.route_response_helpers import api_delpi_success

router = APIRouter(prefix="/knowledge", tags=["Governed Knowledge"])
logger = logging.getLogger(__name__)
_TOPICS = published_knowledge_topics()
_TOPIC_IDS = [topic["id"] for topic in _TOPICS]
_TOPIC_PATTERN = "^(?:" + "|".join(re.escape(topic) for topic in _TOPIC_IDS) + ")$" if _TOPIC_IDS else r"^[a-z][a-z0-9_]{0,63}$"
_TOPIC_DESCRIPTION = "Approved V1 topics: " + "; ".join(
    topic["id"] + " — " + topic["title"] + " (" + ", ".join(topic["aliases"]) + ")"
    for topic in _TOPICS
)


@router.get(
    "/technical-guides/{topic}",
    **GOVERNED_TECHNICAL_KNOWLEDGE,
    response_model=GovernedKnowledgeEnvelope,
)
@require_any_permission([API_DELPI_ACCESS])
def read_governed_technical_knowledge(
    topic: str = Path(..., min_length=1, max_length=64, pattern=_TOPIC_PATTERN,
                      description=_TOPIC_DESCRIPTION, json_schema_extra={"enum": _TOPIC_IDS} if _TOPIC_IDS else {}),
    section: str | None = Query(None, pattern=r"^s[0-9]{4}$", description="Stable heading identifier returned in excerpts, scoped to this source version."),
    subject: str | None = Query(None, min_length=1, max_length=240, description="Optional subject/designation lookup: ranks document sections deterministically by published content (headings weigh more than body; contiguous phrases get a bounded bonus). Returns only matching sections ordered by relevance; empty items with coverage=NO_MATCH when the document has no pertinent excerpt. Combinable with section (subject ranks within that scope)."),
    corpus_version: int = Query(LATEST_CORPUS_VERSION, ge=1, le=1000, description="Corpus version to read. Published: 1 (V1, 15 topics), 2 (V2 adds MP/PI norms). Default is the latest published version; other versions return STALE_VERSION."),
    page: int = Query(1, ge=1, le=10000),
    page_size: int = PAGE_SIZE_QUERY("knowledge_page_3_3"),
):
    try:
        data = build_read_governed_technical_knowledge().execute(
            topic=topic, section=section, corpus_version=corpus_version,
            page=page, page_size=page_size, subject=subject,
        )
    except KnowledgeReadError as exc:
        logger.warning("governed_knowledge_read_failed code=%s", exc.code)
        return error_response(exc.code, status_code=exc.status_code, code=exc.code,
                              recoverable=exc.status_code == 503)
    logger.info("governed_knowledge_read topic=%s page=%s excerpts=%s", topic, page, len(data["items"]))
    return api_delpi_success(data, operation_id="read_governed_technical_knowledge")
