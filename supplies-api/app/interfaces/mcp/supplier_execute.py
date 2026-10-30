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
- per-operation ``idempotency_key`` binds client retries: an in-process
  bounded replay cache returns the previous result instead of writing
  twice, while the durable operation record lives in the api-delpi
  integration tracker (``operation_id`` + ``X-Correlation-ID``);
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
import threading
import time
from collections import OrderedDict
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
from app.interfaces.mcp.constants import (
    EXECUTE_REPLAY_CACHE_SIZE,
    EXECUTE_REPLAY_TTL_SECONDS,
    MAX_IDEMPOTENCY_KEY_LENGTH,
)

logger = logging.getLogger("supplies-api.suri_mcp.execute")

_S2S_GATEWAY = DelpiS2SApiGateway()

_CREATE_PATH = "/integrations/protheus/suppliers"
_UPDATE_PATH = "/integrations/protheus/suppliers/{supplier_id}"
_LIST_PATH = "/supplies/suppliers"

# Per-operation outcome vocabulary — mirrors the BFF write contract plus
# the MCP-level replay marker: confirmed | acknowledged | sent |
# rejected | indeterminate | replayed. ``sent`` means upstream accepted
# transport without a persistence verdict.


class _ReplayCache:
    """Bounded in-process idempotency replay store.

    This is a replay *guard*, not a source of truth: the durable write
    record is the api-delpi integration tracker. Replays within the TTL
    return the previous outcome instead of re-executing the write —
    including ``indeterminate`` results, which are never re-sent blindly.
    """

    def __init__(self, *, ttl_seconds: int, max_size: int) -> None:
        self._ttl = ttl_seconds
        self._max = max_size
        self._lock = threading.Lock()
        self._entries: OrderedDict[str, tuple[float, str, dict[str, Any]]] = (
            OrderedDict()
        )

    @staticmethod
    def _key(user_id: str, action: str, idempotency_key: str) -> str:
        raw = f"{user_id}|{action}|{idempotency_key}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def lookup(
        self, user_id: str, action: str, idempotency_key: str, payload_hash: str
    ) -> str | dict[str, Any] | None:
        """Return the cached op result, ``"conflict"`` on payload mismatch,
        or ``None`` on miss."""
        key = self._key(user_id, action, idempotency_key)
        now = time.monotonic()
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            ts, stored_hash, result = entry
            if now - ts > self._ttl:
                self._entries.pop(key, None)
                return None
            self._entries.move_to_end(key)
            if stored_hash != payload_hash:
                return "conflict"
            return dict(result)

    def store(
        self,
        user_id: str,
        action: str,
        idempotency_key: str,
        payload_hash: str,
        result: dict[str, Any],
    ) -> None:
        key = self._key(user_id, action, idempotency_key)
        now = time.monotonic()
        with self._lock:
            for stale in [
                k for k, (ts, _, _) in self._entries.items() if now - ts > self._ttl
            ]:
                self._entries.pop(stale, None)
            self._entries[key] = (now, payload_hash, dict(result))
            self._entries.move_to_end(key)
            while len(self._entries) > self._max:
                self._entries.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


_REPLAY_CACHE = _ReplayCache(
    ttl_seconds=EXECUTE_REPLAY_TTL_SECONDS,
    max_size=EXECUTE_REPLAY_CACHE_SIZE,
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


def _check_replay(
    user: EffectiveUser,
    action: str,
    index: int,
    op: dict[str, Any],
    idempotency_key: str | None,
) -> dict[str, Any] | None:
    if not idempotency_key:
        return None
    hit = _REPLAY_CACHE.lookup(
        user.id, action, idempotency_key, _payload_hash(op)
    )
    if hit is None:
        return None
    if hit == "conflict":
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
        )
    replayed = dict(hit)
    replayed["index"] = index
    replayed["outcome"] = "replayed"
    replayed["replayed"] = True
    replayed["replayed_outcome"] = hit.get("outcome")
    replayed["idempotency_key"] = idempotency_key
    return replayed


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
        replay = _check_replay(user, action, index, op, idem_key)
        if replay is not None:
            results.append(replay)
            continue
        if action == "create":
            field_names = sorted(str(k) for k in op["supplier"])
            entry = _run_create(user, correlation_id, index, op)
        else:
            field_names = sorted(str(k) for k in op["fields"])
            entry = _run_update(user, correlation_id, index, op)
        if idem_key:
            _REPLAY_CACHE.store(
                user.id, action, idem_key, _payload_hash(op), entry
            )
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
