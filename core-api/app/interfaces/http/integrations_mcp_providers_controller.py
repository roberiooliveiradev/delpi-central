"""S2S eligibility projection of approved MCP providers for DÉLIA.

operationId: list_eligible_mcp_providers

Auth: CORE_API_INTEGRATIONS_SERVICE_TOKEN (shared integrations secret).
Does not return secrets. Does not grant business AuthZ.
"""

from __future__ import annotations

import logging
import time

from flask import Blueprint, jsonify, request

from app.application.use_cases.manage_mcp_providers_use_case import (
    ManageMcpProvidersUseCase,
)
from app.extensions.db import db
from app.extensions.integration_rate_limit import integration_rate_limit
from app.infrastructure.persistence.sqlalchemy.mcp_provider_repository import (
    SqlAlchemyMcpProviderRepository,
)
from app.interfaces.http.security.service_token import require_service_token
from app.interfaces.http.utils.errors import api_error

logger = logging.getLogger(__name__)

integrations_mcp_providers_bp = Blueprint(
    "integrations_mcp_providers",
    __name__,
    url_prefix="/integrations/mcp-providers",
)


@integrations_mcp_providers_bp.route(
    "/eligible",
    methods=["GET"],
    endpoint="list_eligible_mcp_providers",
)
@require_service_token()
@integration_rate_limit()
def list_eligible_mcp_providers():
    """operationId: list_eligible_mcp_providers"""
    started = time.monotonic()
    correlation_id = (
        request.headers.get("X-Correlation-Id")
        or request.headers.get("X-Request-Id")
        or ""
    ).strip() or None
    try:
        items = ManageMcpProvidersUseCase(
            SqlAlchemyMcpProviderRepository(db.session)
        ).list_eligible()
        logger.info(
            "mcp_providers_eligible_ok correlation_id=%s count=%s latency_ms=%.1f",
            correlation_id,
            len(items),
            (time.monotonic() - started) * 1000,
        )
        # R1-RW05: S2S eligibility is provider_approval_only — never
        # user/org connection AuthZ or domain permission.
        return jsonify(
            {
                "items": items,
                "authorizationScope": "provider_approval_only",
            }
        ), 200
    except Exception:
        logger.exception(
            "mcp_providers_eligible_failed correlation_id=%s latency_ms=%.1f",
            correlation_id,
            (time.monotonic() - started) * 1000,
        )
        return api_error(
            "mcp_providers_unavailable",
            "MCP provider registry unavailable",
            status=503,
        )
