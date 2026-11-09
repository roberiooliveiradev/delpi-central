"""Admin HTTP API for Core-governed MCP provider registry.

operationIds (stable):
  list_mcp_providers
  get_mcp_provider
  register_mcp_provider
  review_mcp_provider
  approve_mcp_provider
  reject_mcp_provider
  enable_mcp_provider
  disable_mcp_provider
  revoke_mcp_provider
"""

from __future__ import annotations

from uuid import UUID

from flask import Blueprint, g, jsonify, request

from app.application.use_cases.manage_mcp_providers_use_case import (
    ManageMcpProvidersUseCase,
    McpProviderConflictError,
    McpProviderNotFoundError,
    McpProviderValidationError,
)
from app.extensions.db import db
from app.infrastructure.persistence.sqlalchemy.audit_repository import (
    SqlAlchemyAuditRepository,
)
from app.interfaces.http.security.authorization import require_permission
from app.interfaces.http.utils.errors import api_error

mcp_providers_bp = Blueprint(
    "mcp_providers",
    __name__,
    url_prefix="/admin/mcp-providers",
)


def _actor_user_id() -> UUID | None:
    user = getattr(g, "current_user", None)
    if user is None:
        return None
    raw = getattr(user, "id", None)
    if raw is None:
        return None
    try:
        return UUID(str(raw))
    except Exception:
        return None


def _client_ip() -> str | None:
    return (request.headers.get("X-Forwarded-For") or request.remote_addr or "").split(",")[0].strip() or None


def _use_case() -> ManageMcpProvidersUseCase:
    return ManageMcpProvidersUseCase(
        db.session,
        audit_repository=SqlAlchemyAuditRepository(db.session),
    )


def _expected_version() -> int | None:
    raw = request.args.get("expectedVersion")
    if raw is None and request.is_json:
        body = request.get_json(silent=True) or {}
        raw = body.get("expectedVersion")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except Exception:
        raise McpProviderValidationError(
            "mcp_provider.expected_version_invalid",
            "expectedVersion must be an integer",
            path="expectedVersion",
        )


def _handle(exc: Exception):
    if isinstance(exc, McpProviderValidationError):
        return api_error(exc.code, exc.message, status=400, path=exc.path)
    if isinstance(exc, McpProviderConflictError):
        return api_error(exc.code, exc.message, status=409)
    if isinstance(exc, McpProviderNotFoundError):
        return api_error(
            "mcp_provider.not_found",
            "MCP provider not found",
            status=404,
            path="providerRef",
        )
    raise exc


@mcp_providers_bp.route("", methods=["GET"], endpoint="list_mcp_providers")
@require_permission("mcp_providers.view")
def list_mcp_providers():
    """operationId: list_mcp_providers"""
    try:
        limit = int(request.args.get("limit", 100))
        offset = int(request.args.get("offset", 0))
    except Exception:
        return api_error("validation_error", "limit/offset must be integers", status=400)
    try:
        items = _use_case().list_providers(limit=limit, offset=offset)
        db.session.commit()
        return jsonify({"items": items, "limit": limit, "offset": offset}), 200
    except Exception as exc:
        db.session.rollback()
        return _handle(exc)


@mcp_providers_bp.route("/<provider_ref>", methods=["GET"], endpoint="get_mcp_provider")
@require_permission("mcp_providers.view")
def get_mcp_provider(provider_ref: str):
    """operationId: get_mcp_provider"""
    try:
        item = _use_case().get(provider_ref)
        return jsonify(item), 200
    except Exception as exc:
        return _handle(exc)


@mcp_providers_bp.route("", methods=["POST"], endpoint="register_mcp_provider")
@require_permission("mcp_providers.manage")
def register_mcp_provider():
    """operationId: register_mcp_provider"""
    body = request.get_json(silent=True) or {}
    try:
        item = _use_case().register_candidate(
            provider_ref=body.get("providerRef") or body.get("provider_ref") or "",
            display_name=body.get("displayName") or body.get("display_name") or "",
            endpoint_ref=body.get("endpointRef") or body.get("endpoint_ref") or "",
            owner_ref=body.get("ownerRef") or body.get("owner_ref") or "",
            auth_strategy_ref=body.get("authStrategyRef")
            or body.get("auth_strategy_ref")
            or "KEYCLOAK_DELEGATED",
            resource_client_id=body.get("resourceClientId")
            or body.get("resource_client_id"),
            audience_scope=body.get("audienceScope") or body.get("audience_scope"),
            resource_audience=body.get("resourceAudience")
            or body.get("resource_audience"),
            risk_tier=body.get("riskTier") or body.get("risk_tier"),
            policy_ref=body.get("policyRef") or body.get("policy_ref"),
            actor_user_id=_actor_user_id(),
            ip_address=_client_ip(),
            idempotent=bool(body.get("idempotent", True)),
        )
        db.session.commit()
        return jsonify(item), 201
    except Exception as exc:
        db.session.rollback()
        return _handle(exc)


def _mutation(action: str, provider_ref: str):
    try:
        expected = _expected_version()
        uc = _use_case()
        fn = getattr(uc, action)
        item = fn(
            provider_ref,
            expected_version=expected,
            actor_user_id=_actor_user_id(),
            ip_address=_client_ip(),
        )
        db.session.commit()
        return jsonify(item), 200
    except Exception as exc:
        db.session.rollback()
        return _handle(exc)


@mcp_providers_bp.route(
    "/<provider_ref>/review", methods=["POST"], endpoint="review_mcp_provider"
)
@require_permission("mcp_providers.manage")
def review_mcp_provider(provider_ref: str):
    """operationId: review_mcp_provider"""
    return _mutation("review", provider_ref)


@mcp_providers_bp.route(
    "/<provider_ref>/approve", methods=["POST"], endpoint="approve_mcp_provider"
)
@require_permission("mcp_providers.manage")
def approve_mcp_provider(provider_ref: str):
    """operationId: approve_mcp_provider"""
    return _mutation("approve", provider_ref)


@mcp_providers_bp.route(
    "/<provider_ref>/reject", methods=["POST"], endpoint="reject_mcp_provider"
)
@require_permission("mcp_providers.manage")
def reject_mcp_provider(provider_ref: str):
    """operationId: reject_mcp_provider"""
    return _mutation("reject", provider_ref)


@mcp_providers_bp.route(
    "/<provider_ref>/enable", methods=["POST"], endpoint="enable_mcp_provider"
)
@require_permission("mcp_providers.manage")
def enable_mcp_provider(provider_ref: str):
    """operationId: enable_mcp_provider"""
    return _mutation("enable", provider_ref)


@mcp_providers_bp.route(
    "/<provider_ref>/disable", methods=["POST"], endpoint="disable_mcp_provider"
)
@require_permission("mcp_providers.manage")
def disable_mcp_provider(provider_ref: str):
    """operationId: disable_mcp_provider"""
    return _mutation("disable", provider_ref)


@mcp_providers_bp.route(
    "/<provider_ref>/revoke", methods=["POST"], endpoint="revoke_mcp_provider"
)
@require_permission("mcp_providers.manage")
def revoke_mcp_provider(provider_ref: str):
    """operationId: revoke_mcp_provider"""
    return _mutation("revoke", provider_ref)
