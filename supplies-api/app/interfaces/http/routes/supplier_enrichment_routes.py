"""Supplier enrichment review routes — S2 decision API.

Contract:
    POST   /suppliers/<code>/<store>/enrichment-reviews
    GET    /suppliers/<code>/<store>/enrichment-reviews
    GET    /suppliers/<code>/<store>/enrichment-reviews/<review_id>
    GET    /suppliers/<code>/<store>/enrichment-reviews/<review_id>/decisions
    POST   /suppliers/<code>/<store>/enrichment-reviews/<review_id>/decisions
    POST   /suppliers/<code>/<store>/enrichment-reviews/<review_id>/bulk-decisions
    POST   /suppliers/<code>/<store>/enrichment-reviews/<review_id>/prepare-update

AuthZ: ``supplies.access`` (Core effective) + actor-ownership resource scope
enforced server-side by the review service. No browser-supplied actor, unit,
source or review attributes are honored; no external provider is queried and
no ERP write is ever performed by these routes.
"""

from __future__ import annotations

import uuid
from typing import Any

from flask import Blueprint, g, jsonify, request

from app.application.security.supplies_permissions import can_use_operations
from app.application.services.supplier_enrichment.contracts import (
    EnrichmentSourceUnavailableError,
    IdempotencyConflictError,
    ProposalRecord,
    ReviewAccessDeniedError,
    ReviewNotFoundError,
    ReviewRecord,
    ReviewRevisionConflictError,
    SupplierNotFoundError,
)
from app.application.services.supplier_enrichment.review_service import (
    InvalidDecisionRequestError,
    ProposalNotFoundError,
    SupplierEnrichmentReviewService,
)
from app.application.services.suppliers_dto import normalize_supplier_id
from app.domain.exceptions import EnrichmentUnsupportedDocumentError
from app.domain.supplier_enrichment.review_lifecycle import (
    Decision,
    EnrichmentProposalNotEligibleError,
    EnrichmentProposalNotPendingError,
    EnrichmentReviewNotActionableError,
    EnrichmentStaleBaselineError,
    ReviewStatus,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.infrastructure.gateways.supplier_enrichment_adapters import (
    DelpiCanonicalSupplierReader,
    UnavailableCompanyRegistryProvider,
)
from app.infrastructure.persistence.supplier_enrichment_repository import (
    PostgresSupplierEnrichmentRepository,
)
from app.interfaces.http.auth_decorators import require_policy
from app.interfaces.http.routes.suppliers_routes import (
    _access_token,
    _gateway_error_response,
)

enrichment_bp = Blueprint("supplier_enrichment", __name__)

# Server-owned attributes the browser may never declare.
_SERVER_OWNED_FIELDS = {
    "actor_subject",
    "actor",
    "user_id",
    "unit_context",
    "source_id",
    "source_reference",
    "source_retrieved_at",
    "review_id",
    "created_at",
    "status",
    "revision",
    "snapshot",
    "external_snapshot",
    "external",
}

_MAX_PAGE_SIZE = 50


def _service() -> SupplierEnrichmentReviewService:
    return SupplierEnrichmentReviewService(
        repository=PostgresSupplierEnrichmentRepository(),
        canonical_reader=DelpiCanonicalSupplierReader(),
        registry_provider=UnavailableCompanyRegistryProvider(),
        review_ttl_seconds=Settings.ENRICHMENT_REVIEW_TTL_SECONDS,
    )


def _user():
    return g.current_user


def _normalize_review_id(value: Any) -> str:
    try:
        return str(uuid.UUID(str(value).strip()))
    except (TypeError, ValueError) as exc:
        raise ValueError("review_id must be a UUID") from exc


def _reject_server_fields(body: Any) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise ValueError("request body must be a JSON object")
    forbidden = _SERVER_OWNED_FIELDS & {str(k).strip().lower() for k in body}
    if forbidden:
        raise ValueError(
            "server-owned fields are not client-provided: "
            + ", ".join(sorted(forbidden))
        )
    return body


def _require_decision(body: Any) -> Decision:
    raw = str(body.get("decision") or "").strip().upper()
    try:
        return Decision(raw)
    except ValueError as exc:
        raise ValueError("decision must be ACCEPT or REJECT") from exc


def _require_revision(body: Any) -> int:
    raw = body.get("expected_revision")
    if not isinstance(raw, int) or isinstance(raw, bool) or raw < 1:
        raise ValueError("expected_revision must be a positive integer")
    return raw


def _require_idempotency_key(body: Any) -> str:
    raw = str(body.get("idempotency_key") or "").strip()
    if not raw or len(raw) > 128:
        raise ValueError("idempotency_key must be 1-128 characters")
    return raw


def _optional_reason(body: Any) -> str | None:
    raw = body.get("reason_code")
    if raw is None:
        return None
    value = str(raw).strip()
    if not value or len(value) > 64:
        raise ValueError("reason_code must be 1-64 characters")
    return value


def _review_view(review: ReviewRecord) -> dict[str, Any]:
    return {
        "review_id": review.review_id,
        "supplier_code": review.supplier_code,
        "supplier_store": review.supplier_store,
        "status": review.status,
        "revision": review.revision,
        "actor_subject": review.actor_subject,
        "source_id": review.source_id,
        "source_reference": review.source_reference,
        "source_retrieved_at": _iso(review.source_retrieved_at),
        "mapping_version": review.mapping_version,
        "normalization_version": review.normalization_version,
        "created_at": _iso(review.created_at),
        "updated_at": _iso(review.updated_at),
        "expires_at": _iso(review.expires_at),
    }


def _proposal_view(proposal: ProposalRecord) -> dict[str, Any]:
    return {
        "proposal_id": proposal.proposal_id,
        "field_key": proposal.field_key,
        "section_key": proposal.section_key,
        "comparison_state": proposal.comparison_state,
        "eligibility_state": proposal.eligibility_state,
        "eligibility_reason": proposal.eligibility_reason,
        "source_field": proposal.source_field,
        "source_reference": proposal.source_reference,
        "current_value": proposal.current_value,
        "suggested_value": proposal.suggested_value,
        "decision_state": proposal.decision_state,
    }


def _decision_view(decision) -> dict[str, Any]:
    return {
        "decision_id": decision.decision_id,
        "proposal_id": decision.proposal_id,
        "operation_id": decision.operation_id,
        "field_key": decision.field_key,
        "actor_subject": decision.actor_subject,
        "decision": decision.decision,
        "reason_code": decision.reason_code,
        "decided_at": _iso(decision.decided_at),
        "review_revision": decision.review_revision,
    }


def _iso(value) -> str | None:
    return value.isoformat() if value is not None else None


def _error(exc: Exception):
    """Map domain/application errors to the existing error envelope."""
    if isinstance(exc, ReviewNotFoundError | SupplierNotFoundError | ProposalNotFoundError):
        return jsonify({"detail": str(exc), "code": "not_found"}), 404
    if isinstance(exc, ReviewAccessDeniedError):
        return jsonify({"detail": "Forbidden", "code": "forbidden"}), 403
    if isinstance(exc, EnrichmentSourceUnavailableError):
        return jsonify(
            {"detail": str(exc), "code": "ENRICHMENT_SOURCE_UNAVAILABLE"}
        ), 503
    if isinstance(exc, EnrichmentReviewNotActionableError):
        code = {
            ReviewStatus.EXPIRED: "ENRICHMENT_REVIEW_EXPIRED",
            ReviewStatus.STALE: "ENRICHMENT_STALE_BASELINE",
            ReviewStatus.CANCELLED: "ENRICHMENT_REVIEW_CANCELLED",
        }.get(exc.status, "ENRICHMENT_REVIEW_NOT_ACTIONABLE")
        status = 410 if exc.status is ReviewStatus.EXPIRED else 409
        return jsonify({"detail": str(exc), "code": code}), status
    if isinstance(exc, EnrichmentStaleBaselineError):
        return jsonify({"detail": str(exc), "code": "ENRICHMENT_STALE_BASELINE"}), 409
    if isinstance(exc, ReviewRevisionConflictError):
        return jsonify({"detail": str(exc), "code": "ENRICHMENT_REVISION_CONFLICT"}), 409
    if isinstance(exc, IdempotencyConflictError):
        return jsonify(
            {"detail": "idempotency key reused with different payload",
             "code": "ENRICHMENT_IDEMPOTENCY_CONFLICT"}
        ), 409
    if isinstance(exc, EnrichmentProposalNotPendingError):
        return jsonify({"detail": str(exc), "code": "ENRICHMENT_PROPOSAL_ALREADY_DECIDED"}), 409
    if isinstance(exc, EnrichmentProposalNotEligibleError):
        return jsonify({"detail": str(exc), "code": "ENRICHMENT_PROPOSAL_NOT_ELIGIBLE"}), 422
    if isinstance(exc, EnrichmentUnsupportedDocumentError):
        return jsonify({"detail": str(exc), "code": "ENRICHMENT_UNSUPPORTED_DOCUMENT"}), 422
    if isinstance(exc, InvalidDecisionRequestError | ValueError):
        return jsonify({"detail": str(exc), "code": "invalid_request"}), 422
    if isinstance(exc, DelpiApiGatewayError):
        return _gateway_error_response(exc)
    raise exc


@enrichment_bp.post("/suppliers/<code>/<store>/enrichment-reviews")
@require_policy(can_use_operations)
def create_enrichment_review(code: str, store: str):
    """operationId: create_supplier_enrichment_review.

    Fetches the canonical snapshot, invokes the configured registry source
    port (unavailable in production — 503) and persists the comparison.
    """
    try:
        supplier_id = normalize_supplier_id(code, store)
        _reject_server_fields(request.get_json(silent=True) or {})
        review, proposals = _service().create_review(
            user=_user(),
            supplier_code=supplier_id[:6],
            supplier_store=supplier_id[6:],
            access_token=_access_token(),
        )
        return jsonify(
            {
                "review": _review_view(review),
                "proposals": [_proposal_view(p) for p in proposals],
            }
        ), 201
    except Exception as exc:
        return _error(exc)


@enrichment_bp.get("/suppliers/<code>/<store>/enrichment-reviews")
@require_policy(can_use_operations)
def list_enrichment_reviews(code: str, store: str):
    """operationId: list_supplier_enrichment_reviews — actor-scoped, paginated."""
    try:
        supplier_id = normalize_supplier_id(code, store)
        page = _page(request.args.get("page"), default=1)
        page_size = _page(request.args.get("page_size"), default=20)
        if page_size > _MAX_PAGE_SIZE:
            page_size = _MAX_PAGE_SIZE
        items, total = _service().list_reviews(
            user=_user(),
            supplier_code=supplier_id[:6],
            supplier_store=supplier_id[6:],
            page=page,
            page_size=page_size,
        )
        return jsonify(
            {
                "items": [_review_view(r) for r in items],
                "page": page,
                "page_size": page_size,
                "total": total,
            }
        ), 200
    except Exception as exc:
        return _error(exc)


@enrichment_bp.get(
    "/suppliers/<code>/<store>/enrichment-reviews/<review_id>"
)
@require_policy(can_use_operations)
def get_enrichment_review(code: str, store: str, review_id: str):
    """operationId: get_supplier_enrichment_review."""
    try:
        normalize_supplier_id(code, store)
        normalized = _normalize_review_id(review_id)
        review, proposals = _service().get_review(
            user=_user(), review_id=normalized
        )
        return jsonify(
            {
                "review": _review_view(review),
                "proposals": [_proposal_view(p) for p in proposals],
            }
        ), 200
    except Exception as exc:
        return _error(exc)


@enrichment_bp.get(
    "/suppliers/<code>/<store>/enrichment-reviews/<review_id>/decisions"
)
@require_policy(can_use_operations)
def list_enrichment_decisions(code: str, store: str, review_id: str):
    """operationId: list_supplier_enrichment_decisions — decision history."""
    try:
        normalize_supplier_id(code, store)
        normalized = _normalize_review_id(review_id)
        decisions = _service().list_decisions(
            user=_user(), review_id=normalized
        )
        return jsonify({"items": [_decision_view(d) for d in decisions]}), 200
    except Exception as exc:
        return _error(exc)


@enrichment_bp.post(
    "/suppliers/<code>/<store>/enrichment-reviews/<review_id>/decisions"
)
@require_policy(can_use_operations)
def decide_enrichment_field(code: str, store: str, review_id: str):
    """operationId: decide_supplier_enrichment_field — single decision."""
    try:
        normalize_supplier_id(code, store)
        normalized = _normalize_review_id(review_id)
        body = _reject_server_fields(request.get_json(silent=True))
        field_key = str(body.get("field_key") or "").strip()
        if not field_key:
            raise ValueError("field_key is required")
        review, proposals, replayed = _service().decide(
            user=_user(),
            review_id=normalized,
            field_key=field_key,
            decision=_require_decision(body),
            expected_revision=_require_revision(body),
            idempotency_key=_require_idempotency_key(body),
            reason_code=_optional_reason(body),
        )
        return jsonify(
            {
                "idempotent_replay": replayed,
                "review": _review_view(review),
                "proposals": [_proposal_view(p) for p in proposals],
            }
        ), 200
    except Exception as exc:
        return _error(exc)


@enrichment_bp.post(
    "/suppliers/<code>/<store>/enrichment-reviews/<review_id>/bulk-decisions"
)
@require_policy(can_use_operations)
def decide_enrichment_bulk(code: str, store: str, review_id: str):
    """operationId: decide_supplier_enrichment_fields_bulk — atomic batch."""
    try:
        normalize_supplier_id(code, store)
        normalized = _normalize_review_id(review_id)
        body = _reject_server_fields(request.get_json(silent=True))
        keys = body.get("field_keys")
        if not isinstance(keys, list) or not keys:
            raise ValueError("field_keys must be a non-empty list")
        review, proposals, replayed = _service().decide_bulk(
            user=_user(),
            review_id=normalized,
            decision=_require_decision(body),
            field_keys=[str(k).strip() for k in keys],
            expected_revision=_require_revision(body),
            idempotency_key=_require_idempotency_key(body),
            reason_code=_optional_reason(body),
        )
        return jsonify(
            {
                "idempotent_replay": replayed,
                "review": _review_view(review),
                "proposals": [_proposal_view(p) for p in proposals],
            }
        ), 200
    except Exception as exc:
        return _error(exc)


@enrichment_bp.post(
    "/suppliers/<code>/<store>/enrichment-reviews/<review_id>/prepare-update"
)
@require_policy(can_use_operations)
def prepare_enrichment_update(code: str, store: str, review_id: str):
    """operationId: prepare_supplier_enrichment_update — draft only, no PUT."""
    try:
        normalize_supplier_id(code, store)
        normalized = _normalize_review_id(review_id)
        body = _reject_server_fields(request.get_json(silent=True))
        review, draft = _service().prepare_update(
            user=_user(),
            review_id=normalized,
            expected_revision=_require_revision(body),
            access_token=_access_token(),
        )
        return jsonify(
            {
                "review_id": review.review_id,
                "revision": review.revision,
                "supplier": {
                    "supplier_code": review.supplier_code,
                    "supplier_store": review.supplier_store,
                },
                "baseline_status": "CURRENT",
                "write_gate_enabled": False,
                "draft_fields": [
                    {
                        "field_key": item.field_key,
                        "current_value": item.current_value,
                        "proposed_value": item.proposed_value,
                        "proposal_id": item.proposal_id,
                        "decision_id": item.decision_id,
                    }
                    for item in draft
                ],
            }
        ), 200
    except Exception as exc:
        return _error(exc)


def _page(raw: Any, *, default: int) -> int:
    try:
        value = int(str(raw or default))
    except (TypeError, ValueError) as exc:
        raise ValueError("pagination parameters must be integers") from exc
    if value < 1:
        raise ValueError("pagination parameters must be positive")
    return value
