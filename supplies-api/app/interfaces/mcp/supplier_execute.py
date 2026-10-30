"""SURI execute — governed supplier writes with Portal parity.

Closed ``(entity, action)`` registry for ``execute(entity="suppliers",
action="create"|"update")``. The same canonical building blocks the Flask
BFF routes use are reused here — ``DelpiS2SApiGateway`` (individual S2S
credential, never the shared legacy token), ``sanitize_post_body`` /
``sanitize_put_body`` / ``normalize_supplier_id`` and
``classify_supplier_write_error`` — so validation, editable-field rules,
upstream error semantics and the honest outcome vocabulary
(``confirmed``/``acknowledged``/``rejected``/``indeterminate``) stay a
single source of truth.

Governance guarantees:

- server-side authorization was already enforced by the caller
  (``can_use_operations`` on the user's own effective identity — the
  same policy the Portal write routes apply);
- per-operation ``idempotency_key`` binds client retries: a durable,
  atomic claim row in ``supplies.suri_execute_operations`` (V005) makes
  check-then-act safe across processes, workers and restarts — the first
  claim wins, same-key callers get ``replay``/``in_progress``/
  ``conflict`` and never re-execute; the api-delpi integration tracker
  (``operation_id`` + ``X-Correlation-ID``) remains the write record;
- creates run the same advisory duplicate pre-check the Portal performs
  (tax_id search over the governed list read) before any write byte;
- every executed operation emits one structured audit line — actor,
  action, normalized identity, field names (never values), outcome and
  tracking ids;
- failures never retry a write implicitly: ``indeterminate`` outcomes
  are reported so the caller verifies via ``operation_id`` first.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import timedelta
from typing import Any
from uuid import uuid4

from app.application.services.suppliers_dto import (
    POST_SUPPLIER_FIELDS,
    classify_supplier_write_error,
    digits_only,
    normalize_supplier_id,
    sanitize_post_body,
    sanitize_put_body,
)
from app.domain.entities import EffectiveUser
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.infrastructure.gateways.delpi_envelope import unwrap_delpi_envelope
from app.infrastructure.gateways.delpi_s2s_gateway import DelpiS2SApiGateway
from app.infrastructure.persistence.suri_execute_operations_repository import (
    PostgresSuriExecuteOperationsRepository,
)
from app.interfaces.mcp.constants import (
    EXECUTE_IDEMPOTENCY_TTL_HOURS,
    MAX_IDEMPOTENCY_KEY_LENGTH,
)

logger = logging.getLogger("supplies-api.suri_mcp.execute")

_S2S_GATEWAY = DelpiS2SApiGateway()

_CREATE_PATH = "/integrations/protheus/suppliers"
_UPDATE_PATH = "/integrations/protheus/suppliers/{supplier_id}"
_LIST_PATH = "/supplies/suppliers"

# Per-operation outcome vocabulary — mirrors the BFF write contract plus
# MCP-level markers: confirmed | acknowledged | sent | rejected |
# indeterminate | replayed | in_progress. ``sent`` means upstream
# accepted transport without a persistence verdict; ``in_progress``
# means an identical-keyed operation is still in flight or its claim
# could not be resolved — never re-executed blindly.

_IDEMPOTENCY_STORE = PostgresSuriExecuteOperationsRepository(
    ttl=timedelta(hours=EXECUTE_IDEMPOTENCY_TTL_HOURS)
)


def _payload_hash(op: dict[str, Any]) -> str:
    canonical = {k: v for k, v in op.items() if k != "idempotency_key"}
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def _op_error(
    index: int,
    *,
    outcome: str,
    code: str,
    message: str,
    fields: list | None = None,
    idempotency_key: str | None = None,
    http_status: int | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "index": index,
        "outcome": outcome,
        "replayed": False,
        "error": {"code": code, "message": message},
        "idempotency_key": idempotency_key,
    }
    if fields:
        entry["error"]["fields"] = fields
    if http_status is not None:
        entry["http_status"] = http_status
    return entry


def _audit(
    user: EffectiveUser,
    *,
    correlation_id: str,
    action: str,
    entry: dict[str, Any],
    field_names: list[str] | None,
) -> None:
    """One structured audit line per operation — identity and field names
    only; supplier payload values (LGPD-sensitive) are never logged."""
    logger.info(
        "suri_execute actor=%s correlation=%s action=%s index=%s "
        "supplier_id=%s fields=%s outcome=%s operation_id=%s "
        "http_status=%s idem=%s",
        user.id,
        correlation_id,
        action,
        entry.get("index"),
        entry.get("supplier_id") or "-",
        ",".join(sorted(field_names or [])) or "-",
        entry.get("outcome"),
        entry.get("operation_id") or "-",
        entry.get("http_status") or "-",
        hashlib.sha256(
            str(entry.get("idempotency_key") or "").encode("utf-8")
        ).hexdigest()[:12]
        if entry.get("idempotency_key")
        else "-",
    )


def _validation_reject(
    index: int, idempotency_key: str | None, message: str, code: str = "invalid_request"
) -> dict[str, Any]:
    return _op_error(
        index,
        outcome="rejected",
        code=code,
        message=message,
        idempotency_key=idempotency_key,
        http_status=422,
    )


def _claim_or_replay(
    user: EffectiveUser,
    action: str,
    index: int,
    op: dict[str, Any],
    idempotency_key: str | None,
    correlation_id: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Durable idempotency claim — returns ``(entry, claim_operation_id)``.

    ``entry`` is a terminal per-operation result (replay/conflict/
    in_progress/store failure) and ``claim_operation_id`` stays ``None``;
    on a fresh claim ``entry`` is ``None`` and the caller MUST execute
    the write then ``complete()`` the claim row. Any store error fails
    closed — a keyed write is never issued without a successful claim.
    """
    if not idempotency_key:
        return None, None
    try:
        claim = _IDEMPOTENCY_STORE.claim(
            actor_subject=str(user.id),
            entity="suppliers",
            action=action,
            idempotency_key=str(idempotency_key),
            payload_hash=_payload_hash(op),
            correlation_id=correlation_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "suri_execute idempotency_store_unavailable error=%s",
            type(exc).__name__,
        )
        return _op_error(
            index,
            outcome="indeterminate",
            code="idempotency_store_unavailable",
            message=(
                "The durable idempotency store is unavailable — the "
                "write was not sent. Retry later with the same "
                "idempotency_key or verify the operation first."
            ),
            idempotency_key=idempotency_key,
            http_status=503,
        ), None
    if claim.kind == "claimed":
        return None, claim.operation_id
    if claim.kind == "conflict":
        return _op_error(
            index,
            outcome="rejected",
            code="idempotency_conflict",
            message=(
                "idempotency key reused with a different payload — "
                "the previous operation was not repeated."
            ),
            idempotency_key=idempotency_key,
            http_status=409,
        ), None
    if claim.kind == "in_progress":
        return _op_error(
            index,
            outcome="in_progress",
            code="operation_in_progress",
            message=(
                "An operation with the same idempotency key is still "
                "in flight or could not be confirmed — it was NOT "
                "re-executed. Verify via operation_id/tracker before "
                "retrying."
            ),
            idempotency_key=idempotency_key,
            http_status=409,
        ), None
    stored = dict(claim.result or {})
    stored["index"] = index
    stored["outcome"] = "replayed"
    stored["replayed"] = True
    stored["replayed_outcome"] = stored.get("replayed_outcome") or (
        claim.result or {}
    ).get("outcome")
    stored["idempotency_key"] = idempotency_key
    return stored, None


def _complete_claim(claim_operation_id: str | None, entry: dict[str, Any]) -> None:
    """Persist the sanitized operation result on the claim row.

    The stored result carries outcome/operation_id/supplier_id/status —
    never payload values. A complete failure keeps the claim in
    'in_progress' (never reclaimed, never re-executed) and is logged so
    the tracker reconciles it.
    """
    if not claim_operation_id:
        return
    try:
        _IDEMPOTENCY_STORE.complete(
            operation_id=claim_operation_id, result=entry
        )
    except Exception:  # noqa: BLE001
        logger.warning(
            "suri_execute idempotency_complete_failed claim=%s",
            claim_operation_id,
        )


def _duplicate_precheck(user: EffectiveUser, supplier: dict[str, Any]) -> str | None:
    """Advisory duplicate guard — the same tax_id search the Portal
    performs before creation. Only comparable for CNPJ (public registry,
    published unmasked); masked documents defer to the upstream contract.
    Returns the matching supplier_id on hit, else ``None``. Failures of
    the read are non-blocking — the upstream write stays authoritative.
    """
    tax_digits = digits_only(supplier.get("tax_id"))
    if len(tax_digits) != 14:
        return None
    try:
        payload = _S2S_GATEWAY.get(
            _LIST_PATH,
            access_token=user.access_token or "",
            params={"query": tax_digits, "page_size": "10"},
        )
    except DelpiApiGatewayError as exc:
        logger.warning(
            "suri_execute duplicate_precheck_unavailable code=%s",
            exc.code or exc.status_code or "transport",
        )
        return None
    data = unwrap_delpi_envelope(payload)
    items = data.get("items") if isinstance(data, dict) else None
    for item in items or []:
        if not isinstance(item, dict):
            continue
        if digits_only(item.get("tax_id")) == tax_digits:
            code = str(item.get("supplier_code") or "").strip()
            store = str(item.get("supplier_store") or "").strip()
            return f"{code}{store}".strip() or "existing"
    return None


def _gateway_write_error(
    index: int,
    exc: DelpiApiGatewayError,
    *,
    idempotency_key: str | None,
) -> dict[str, Any]:
    classification = classify_supplier_write_error(exc)
    message = classification["detail"]
    return _op_error(
        index,
        outcome=classification["outcome"] or "indeterminate",
        code=classification["code"],
        message=message,
        fields=classification["fields"] or None,
        idempotency_key=idempotency_key,
        http_status=classification["status"],
    )


def _success_entry(
    index: int,
    *,
    data: dict[str, Any],
    persistence_flag: str,
    ack_flag: str | None,
    supplier_id: str | None,
    idempotency_key: str | None,
) -> dict[str, Any]:
    proven = bool(data.get(persistence_flag))
    acknowledged = bool(data.get(ack_flag)) if ack_flag else True
    outcome = "confirmed" if proven else ("acknowledged" if acknowledged else "sent")
    entry: dict[str, Any] = {
        "index": index,
        "outcome": outcome,
        "replayed": False,
        "acknowledged": acknowledged,
        "persistence_proven": proven,
        "operation_id": data.get("operation_id"),
        "tracking_warning": data.get("tracking_warning"),
        "supplier_id": supplier_id,
        "idempotency_key": idempotency_key,
    }
    return {k: v for k, v in entry.items() if v is not None or k in {
        "index", "outcome", "replayed", "acknowledged", "persistence_proven",
        "idempotency_key",
    }}


def _run_create(
    user: EffectiveUser,
    correlation_id: str,
    index: int,
    op: dict[str, Any],
) -> dict[str, Any]:
    key = op.get("idempotency_key")
    supplier = op.get("supplier")
    unknown = {str(k) for k in supplier} - set(POST_SUPPLIER_FIELDS)
    if unknown:
        return _validation_reject(
            index,
            key,
            "fields not allowed for supplier create: "
            + ", ".join(sorted(unknown)),
        )
    try:
        fornecedor = sanitize_post_body({"fornecedor": supplier})
    except ValueError as exc:
        return _validation_reject(index, key, str(exc))
    if not fornecedor:
        return _validation_reject(index, key, "supplier payload is empty")

    duplicate = _duplicate_precheck(user, fornecedor)
    if duplicate:
        return _op_error(
            index,
            outcome="rejected",
            code="supplier_duplicate_tax_id",
            message=(
                "A supplier with the same tax_id already exists "
                f"(supplier_id={duplicate}). Use execute action=update "
                "for cadastral changes."
            ),
            idempotency_key=key,
            http_status=409,
        )

    try:
        payload = _S2S_GATEWAY.post(
            _CREATE_PATH,
            access_token=user.access_token or "",
            json_body={"fornecedor": fornecedor},
            correlation_id=correlation_id,
        )
    except DelpiApiGatewayError as exc:
        return _gateway_write_error(index, exc, idempotency_key=key)
    data = unwrap_delpi_envelope(payload)
    if not isinstance(data, dict):
        data = {}
    supplier_code = data.get("supplier_code")
    supplier_store = data.get("supplier_store")
    resource = (
        f"{supplier_code}{supplier_store}"
        if supplier_code and supplier_store
        else None
    )
    return _success_entry(
        index,
        data=data,
        persistence_flag="creation_confirmed",
        ack_flag=None,
        supplier_id=resource,
        idempotency_key=key,
    )


def _run_update(
    user: EffectiveUser,
    correlation_id: str,
    index: int,
    op: dict[str, Any],
) -> dict[str, Any]:
    key = op.get("idempotency_key")
    try:
        supplier_id = normalize_supplier_id(
            op.get("supplier_code"), op.get("supplier_store")
        )
    except ValueError as exc:
        return _validation_reject(index, key, str(exc), code="invalid_identity")
    try:
        fornecedor = sanitize_put_body({"fornecedor": op.get("fields")})
    except ValueError as exc:
        return _validation_reject(index, key, str(exc))

    try:
        payload = _S2S_GATEWAY.put(
            _UPDATE_PATH.format(supplier_id=supplier_id),
            access_token=user.access_token or "",
            json_body={"fornecedor": fornecedor},
            correlation_id=correlation_id,
        )
    except DelpiApiGatewayError as exc:
        entry = _gateway_write_error(index, exc, idempotency_key=key)
        entry["supplier_id"] = supplier_id
        return entry
    data = unwrap_delpi_envelope(payload)
    if not isinstance(data, dict):
        data = {}
    return _success_entry(
        index,
        data=data,
        persistence_flag="persistence_proven",
        ack_flag="update_acknowledged",
        supplier_id=supplier_id,
        idempotency_key=key,
    )


def _shape_errors(action: str, index: int, op: dict[str, Any]) -> dict[str, Any] | None:
    """Per-action shape rules — keep create/update contracts disjoint."""
    key = op.get("idempotency_key")
    if key is not None and not (0 < len(str(key).strip()) <= MAX_IDEMPOTENCY_KEY_LENGTH):
        return _validation_reject(
            index, None, "idempotency_key must be 1-128 characters"
        )
    if action == "create":
        forbidden = [
            k for k in ("supplier_code", "supplier_store", "fields") if op.get(k)
        ]
        if forbidden:
            return _validation_reject(
                index,
                key,
                "action=create does not accept: " + ", ".join(forbidden)
                + " — provide only 'supplier'.",
            )
        supplier = op.get("supplier")
        if not isinstance(supplier, dict) or not supplier:
            return _validation_reject(
                index, key, "action=create requires a non-empty 'supplier' object."
            )
        return None
    forbidden = [k for k in ("supplier",) if op.get(k)]
    if forbidden:
        return _validation_reject(
            index,
            key,
            "action=update does not accept 'supplier' — provide "
            "'supplier_code', 'supplier_store' and 'fields'.",
        )
    if not (str(op.get("supplier_code") or "").strip()) or not (
        str(op.get("supplier_store") or "").strip()
    ):
        return _validation_reject(
            index,
            key,
            "action=update requires unequivocal identity: "
            "supplier_code and supplier_store.",
            code="invalid_identity",
        )
    fields = op.get("fields")
    if not isinstance(fields, dict) or not fields:
        return _validation_reject(
            index, key, "action=update requires a non-empty 'fields' object."
        )
    return None


def execute_supplier_write(
    user: EffectiveUser,
    *,
    action: str,
    operations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Run a batch of governed supplier writes for one (entity, action).

    Operations execute sequentially; each gets an isolated outcome — no
    distributed transaction is presumed and no rejected/indeterminate op
    produces side effects beyond the canonical tracking record.
    """
    correlation_id = str(uuid4())
    results: list[dict[str, Any]] = []
    for index, op in enumerate(operations):
        field_names: list[str] | None = None
        shape_error = _shape_errors(action, index, op)
        if shape_error is not None:
            results.append(shape_error)
            _audit(
                user,
                correlation_id=correlation_id,
                action=action,
                entry=shape_error,
                field_names=None,
            )
            continue
        idem_key = op.get("idempotency_key")
        replay, claim_id = _claim_or_replay(
            user, action, index, op, idem_key, correlation_id
        )
        if replay is not None:
            results.append(replay)
            _audit(
                user,
                correlation_id=correlation_id,
                action=action,
                entry=replay,
                field_names=None,
            )
            continue
        if action == "create":
            field_names = sorted(str(k) for k in op["supplier"])
            entry = _run_create(user, correlation_id, index, op)
        else:
            field_names = sorted(str(k) for k in op["fields"])
            entry = _run_update(user, correlation_id, index, op)
        _complete_claim(claim_id, entry)
        results.append(entry)
        _audit(
            user,
            correlation_id=correlation_id,
            action=action,
            entry=entry,
            field_names=field_names,
        )

    summary = {"total": len(results)}
    for entry in results:
        outcome = str(entry.get("outcome") or "indeterminate")
        summary[outcome] = summary.get(outcome, 0) + 1
    return {
        "entity": "suppliers",
        "action": action,
        "correlation_id": correlation_id,
        "summary": summary,
        "operations": results,
        "notes": [
            "persistence_proven/confirmed means the api-delpi read-back "
            "verified the write; acknowledged/sent means upstream accepted "
            "but confirmation is pending — verify via operation_id.",
            "indeterminate means transport uncertainty — check the "
            "operation before retrying; nothing is retried implicitly.",
        ],
    }
