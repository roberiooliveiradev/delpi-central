"""Governed supplier-enrichment writes for SURI ``execute``.

Same ACT machinery as ``supplier_execute``/``comex_execute``: durable V005
claim per operation, structured audit, closed operation keys, caller
identity only. Delegates to the canonical ``SupplierEnrichmentReviewService``
— same owner as the BFF routes, including the actor rate limiter and the
supplier_id normalization used by ``/suppliers/<code>/<store>/*`` routes.
"""

from __future__ import annotations

import logging
import uuid as _uuid
from typing import Any

from app.interfaces.mcp.supplier_execute import (
    _audit,
    _claim_or_replay,
    _complete_claim,
    _op_error,
)
from app.application.services.supplier_enrichment.review_service import (
    SupplierEnrichmentReviewService,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.gateways.supplier_enrichment_adapters import (
    DelpiCanonicalSupplierReader,
    company_registry_provider,
)
from app.infrastructure.persistence.supplier_enrichment_repository import (
    PostgresSupplierEnrichmentRepository,
)
from app.application.services.suppliers_dto import normalize_supplier_id
from app.infrastructure.gateways.brasilapi_registry_provider import (
    registry_rate_limiter,
)
from app.domain.entities import EffectiveUser
from app.domain.supplier_enrichment.review_lifecycle import Decision

logger = logging.getLogger("supplies-api.suri_mcp.execute")

def _service() -> SupplierEnrichmentReviewService:
    return SupplierEnrichmentReviewService(
        repository=PostgresSupplierEnrichmentRepository(),
        canonical_reader=DelpiCanonicalSupplierReader(),
        registry_provider=company_registry_provider(),
        review_ttl_seconds=Settings.ENRICHMENT_REVIEW_TTL_SECONDS,
    )

_SUPPLIER_KEYS = {"supplier_code", "supplier_store"}
_REVIEW_CREATE_KEYS = frozenset(
    {"idempotency_key"} | _SUPPLIER_KEYS
)
_DECIDE_KEYS = frozenset(
    {
        "idempotency_key", "review_id", "field_key", "decision",
        "expected_revision", "reason_code",
    } | _SUPPLIER_KEYS
)
_DECIDE_BULK_KEYS = frozenset(
    {
        "idempotency_key", "review_id", "field_keys", "decision",
        "expected_revision", "reason_code",
    } | _SUPPLIER_KEYS
)
_PREPARE_KEYS = frozenset(
    {
        "idempotency_key", "review_id", "expected_revision",
    } | _SUPPLIER_KEYS
)

ENRICHMENT_WRITE_KEYS_BY_ACTION = {
    "review_create": _REVIEW_CREATE_KEYS,
    "decide": _DECIDE_KEYS,
    "decide_bulk": _DECIDE_BULK_KEYS,
    "prepare_update": _PREPARE_KEYS,
}


def _decision(value: Any) -> Decision:
    try:
        return Decision(str(value or "").strip().upper())
    except ValueError:
        raise ValueError("decision must be ACCEPT or REJECT")


def _exec_op(user: EffectiveUser, action: str, op: dict[str, Any]) -> dict:
    code = str(op.get("supplier_code") or "")
    store = str(op.get("supplier_store") or "")
    sid = normalize_supplier_id(code, store)
    supplier_code, supplier_store = sid[:6], sid[6:]
    if action == "review_create":
        registry_rate_limiter().acquire("actor", str(user.id))
        review, proposals = _service().create_review(
            user=user,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
            access_token=user.access_token or "",
        )
        return {
            "review_id": review.review_id,
            "status": str(getattr(review, "status", "") or ""),
            "proposals": len(proposals),
        }
    if action == "decide":
        review, proposals, replayed = _service().decide(
            user=user,
            review_id=str(op.get("review_id") or ""),
            field_key=str(op.get("field_key") or ""),
            decision=_decision(op.get("decision")),
            expected_revision=int(op.get("expected_revision")),
            idempotency_key=str(op.get("idempotency_key") or ""),
            reason_code=op.get("reason_code"),
        )
        return {
            "review_id": review.review_id,
            "status": str(getattr(review, "status", "") or ""),
            "decisions_replayed": replayed,
        }
    if action == "decide_bulk":
        review, proposals, replayed = _service().decide_bulk(
            user=user,
            review_id=str(op.get("review_id") or ""),
            decision=_decision(op.get("decision")),
            field_keys=op.get("field_keys") or [],
            expected_revision=int(op.get("expected_revision")),
            idempotency_key=str(op.get("idempotency_key") or ""),
            reason_code=op.get("reason_code"),
        )
        return {
            "review_id": review.review_id,
            "status": str(getattr(review, "status", "") or ""),
            "decisions_replayed": replayed,
        }
    review, draft = _service().prepare_update(
        user=user,
        review_id=str(op.get("review_id") or ""),
        expected_revision=int(op.get("expected_revision")),
        access_token=user.access_token or "",
    )
    return {
        "review_id": review.review_id,
        "status": str(getattr(review, "status", "") or ""),
        "draft_items": len(draft or []),
    }


def execute_enrichment_write(
    user: EffectiveUser, *, action: str, operations: list[dict[str, Any]]
) -> dict[str, Any]:
    correlation_id = str(_uuid.uuid4())
    results: list[dict[str, Any]] = []
    for index, op in enumerate(operations):
        idem_key = op.get("idempotency_key")
        entry, claim_id = _claim_or_replay(
            user, action, index, op, idem_key, correlation_id
        )
        if entry is not None:
            _audit(user, correlation_id=correlation_id, action=action,
                   entry=entry,
                   field_names=sorted(
                       k for k in op if k != "idempotency_key"))
            results.append(entry)
            continue
        try:
            payload = _exec_op(user, action, op)
        except ValueError as exc:
            entry = _op_error(
                index, outcome="rejected",
                code="invalid_request", message=str(exc),
                idempotency_key=idem_key, http_status=422)
        except Exception as exc:
            name = type(exc).__name__.lower()
            if "notfound" in name or "not_found" in name:
                code_, status = "not_found", 404
            elif "denied" in name or "forbidden" in name:
                code_, status = "forbidden", 403
            elif ("conflict" in name or "revision" in name
                    or "stale" in name or "idempotency" in name
                    or "invalid" in name or "actionable" in name
                    or "unsupported" in name or "rate" in name):
                code_, status = name.replace("error", "") or "conflict", 409
            else:
                code_, status = None, 0
            if code_:
                entry = _op_error(
                    index, outcome="rejected", code=code_,
                    message=str(exc), idempotency_key=idem_key,
                    http_status=status)
            else:
                entry = _op_error(
                    index, outcome="indeterminate",
                    code="upstream_error",
                    message=("Upstream did not confirm the write — verify "
                             "before retrying with the same "
                             "idempotency_key."),
                    idempotency_key=idem_key, http_status=502)
        else:
            entry = {
                "index": index, "outcome": "confirmed",
                "idempotency_key": idem_key, **payload,
            }
        _complete_claim(claim_id, entry)
        _audit(user, correlation_id=correlation_id, action=action,
               entry=entry,
               field_names=sorted(k for k in op if k != "idempotency_key"))
        results.append(entry)
    confirmed = sum(1 for r in results if r.get("outcome") == "confirmed")
    return {
        "success": all(
            r.get("outcome") in {"confirmed", "replayed"} for r in results
        ),
        "correlation_id": correlation_id,
        "entity": "enrichment",
        "action": action,
        "operations_total": len(results),
        "operations_confirmed": confirmed,
        "results": results,
    }
