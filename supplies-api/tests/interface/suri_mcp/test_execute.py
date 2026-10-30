"""SURI execute — governed supplier write surface (rev.3).

Covers the semantic contract: closed (entity, action) registry, per-op
shape rules, canonical allowlist/identity enforcement, authorization
parity, idempotent replay, multi-operation isolation, upstream error
mapping and honest outcomes — all with mocked gateways, never real
upstream writes.
"""

from __future__ import annotations

import pytest
from suri_mcp.suri_fixtures import make_context, make_user_ns

from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.interfaces.mcp import supplier_execute, tool_bridge


class FakeS2SGateway:
    """Captures get/post/put and replays canned api-delpi payloads."""

    def __init__(self, *, post=None, put=None, get=None, error=None, get_error=None):
        self.post_payload = post
        self.put_payload = put
        self.get_payload = get
        self.error = error
        self.get_error = get_error
        self.calls: list[dict] = []

    def _maybe_raise(self, error):
        if error is not None:
            raise error

    def get(self, path, *, access_token, params=None):
        self.calls.append({"method": "GET", "path": path, "params": params})
        self._maybe_raise(self.get_error or self.error)
        return self.get_payload

    def post(self, path, *, access_token, json_body, correlation_id=None):
        self.calls.append(
            {
                "method": "POST",
                "path": path,
                "json_body": json_body,
                "correlation_id": correlation_id,
            }
        )
        self._maybe_raise(self.error)
        return self.post_payload

    def put(self, path, *, access_token, json_body, correlation_id=None):
        self.calls.append(
            {
                "method": "PUT",
                "path": path,
                "json_body": json_body,
                "correlation_id": correlation_id,
            }
        )
        self._maybe_raise(self.error)
        return self.put_payload


CREATE_PAYLOAD = {
    "success": True,
    "data": {
        "codusr": "000304",
        "supplier_store": "01",
        "supplier_code": "000123",
        "operation_id": "11111111-2222-3333-4444-555555555555",
        "creation_confirmed": True,
    },
}

UPDATE_PAYLOAD = {
    "success": True,
    "data": {
        "operation_id": "66666666-7777-8888-9999-000000000000",
        "update_acknowledged": True,
        "persistence_proven": True,
    },
}

EMPTY_LIST = {"success": True, "data": {"items": [], "total": 0}}

DUP_LIST = {
    "success": True,
    "data": {
        "items": [
            {
                "supplier_code": "000777",
                "supplier_store": "01",
                "supplier_name": "EXISTING LTDA",
                "tax_id": "11222333000181",
            }
        ],
        "total": 1,
    },
}

VALID_CREATE_SUPPLIER = {
    "supplier_store": "01",
    "person_type": "J",
    "tax_id": "11222333000181",
    "supplier_name": "ACME LTDA",
    "supplier_short_name": "ACME",
    "country_code": "105",
    "bacen_country_code": "01058",
    "payment_condition_code": "001",
    "payment_method_code": "01",
    "financial_nature_code": "001",
    "accounting_account": "21101001",
    "rohs_indicator": "N",
}


class FakeIdempotencyStore:
    """Durable-store stand-in honoring the repository contract.

    Postgres provides the atomic UNIQUE claim (covered by the pg suite);
    this fake preserves the *durable* semantics — state survives call
    boundaries exactly like a real row, so replay/conflict/in_progress
    never depend on in-process memory.
    """

    def __init__(self, *, fail_claim=False, fail_complete=False):
        self.rows: dict[tuple, dict] = {}
        self.fail_claim = fail_claim
        self.fail_complete = fail_complete
        self.claim_calls = 0
        self.complete_calls = 0

    def claim(self, *, actor_subject, entity, action, idempotency_key,
              payload_hash, correlation_id):
        from app.infrastructure.persistence.suri_execute_operations_repository import (
            ExecuteClaim,
        )

        self.claim_calls += 1
        if self.fail_claim:
            raise RuntimeError("store down")
        key = (actor_subject, entity, action, idempotency_key)
        row = self.rows.get(key)
        if row is None:
            operation_id = f"claim-{len(self.rows)}"
            self.rows[key] = {
                "operation_id": operation_id,
                "payload_hash": payload_hash,
                "status": "in_progress",
                "result": None,
            }
            return ExecuteClaim(kind="claimed", operation_id=operation_id)
        if row["payload_hash"] != payload_hash:
            return ExecuteClaim(kind="conflict")
        if row["status"] == "completed":
            return ExecuteClaim(
                kind="replay",
                operation_id=row["operation_id"],
                result=row["result"],
            )
        return ExecuteClaim(kind="in_progress", operation_id=row["operation_id"])

    def complete(self, *, operation_id, result):
        self.complete_calls += 1
        if self.fail_complete:
            raise RuntimeError("complete failed")
        for row in self.rows.values():
            if row["operation_id"] == operation_id:
                row["status"] = "completed"
                row["result"] = result

    def seed_in_progress(self, *, actor_subject, entity, action,
                         idempotency_key, payload_hash):
        self.rows[(actor_subject, entity, action, idempotency_key)] = {
            "operation_id": "claim-stuck",
            "payload_hash": payload_hash,
            "status": "in_progress",
            "result": None,
        }


@pytest.fixture()
def idem_store(monkeypatch):
    def _install(**kwargs) -> FakeIdempotencyStore:
        store = FakeIdempotencyStore(**kwargs)
        monkeypatch.setattr(supplier_execute, "_IDEMPOTENCY_STORE", store)
        return store

    return _install


@pytest.fixture(autouse=True)
def _durable_idem_store(idem_store):
    idem_store()
    yield


@pytest.fixture()
def s2s(monkeypatch):
    def _install(**kwargs) -> FakeS2SGateway:
        gw = FakeS2SGateway(**kwargs)
        monkeypatch.setattr(supplier_execute, "_S2S_GATEWAY", gw)
        return gw

    return _install


def _call(*args):
    """Production-equivalent invocation — server._guarded maps exceptions
    through handle_tool_error, so tests exercise the same boundary."""
    try:
        return tool_bridge.tool_execute(*args)
    except Exception as exc:  # noqa: BLE001
        return tool_bridge.handle_tool_error(exc)


def _unwrap(result):
    content = result.content[0]
    import json

    return json.loads(content.text)


def _ops_data(result):
    return _unwrap(result)["data"]


def _op(data, index):
    return data["operations"][index]


# -- closed registry --------------------------------------------------------


def test_execute_unknown_entity_rejected(access_context):
    access_context()
    result = _call("purchase_orders", "create", [])
    assert _unwrap(result)["success"] is False


def test_execute_unknown_action_rejected(access_context):
    access_context()
    result = _call("suppliers", "delete", [])
    assert _unwrap(result)["success"] is False


def test_execute_requires_operations(access_context):
    access_context()
    result = _call("suppliers", "create", [])
    assert _unwrap(result)["success"] is False


def test_execute_batch_limit(access_context):
    access_context()
    ops = [{"supplier": {"a": "1"}}] * 11
    result = _call("suppliers", "create", ops)
    assert _unwrap(result)["success"] is False


def test_execute_unknown_operation_keys_rejected(access_context):
    access_context()
    ops = [{"supplier": {"a": "1"}, "admin_override": True}]
    result = _call("suppliers", "create", ops)
    assert _unwrap(result)["success"] is False


# -- authorization ----------------------------------------------------------


def test_execute_forbidden_without_supplies_access(no_access_context):
    result = _call(
        "suppliers", "create", [{"supplier": VALID_CREATE_SUPPLIER}]
    )
    body = _unwrap(result)
    assert body["success"] is False
    assert body["status_code"] == 403


def test_execute_forbidden_for_service_principal(monkeypatch):
    ns = make_user_ns(permissions=["supplies.access"], principal_type="service")
    monkeypatch.setattr(
        tool_bridge, "require_mcp_context", lambda: make_context(ns)
    )
    result = _call(
        "suppliers", "create", [{"supplier": VALID_CREATE_SUPPLIER}]
    )
    body = _unwrap(result)
    assert body["success"] is False
    assert body["status_code"] == 403


def test_execute_anonymous_unauthenticated(anonymous_context):
    result = _call(
        "suppliers", "create", [{"supplier": VALID_CREATE_SUPPLIER}]
    )
    body = _unwrap(result)
    assert body["success"] is False
    assert body["status_code"] == 401


# -- create ------------------------------------------------------------------


def test_create_confirmed(access_context, s2s):
    access_context()
    gw = s2s(post=CREATE_PAYLOAD, get=EMPTY_LIST)
    result = _call(
        "suppliers", "create", [{"supplier": dict(VALID_CREATE_SUPPLIER)}]
    )
    data = _ops_data(result)
    assert data["action"] == "create"
    op = _op(data, 0)
    assert op["outcome"] == "confirmed"
    assert op["persistence_proven"] is True
    assert op["operation_id"] == CREATE_PAYLOAD["data"]["operation_id"]
    assert op["supplier_id"] == "00012301"
    post_calls = [c for c in gw.calls if c["method"] == "POST"]
    assert len(post_calls) == 1
    assert post_calls[0]["path"] == "/integrations/protheus/suppliers"
    assert post_calls[0]["json_body"]["fornecedor"]["tax_id"] == "11222333000181"
    assert post_calls[0]["correlation_id"] == data["correlation_id"]


def test_create_rejects_unknown_field(access_context, s2s):
    access_context()
    gw = s2s(post=CREATE_PAYLOAD, get=EMPTY_LIST)
    op = {"supplier": {**VALID_CREATE_SUPPLIER, "hack_field": "x"}}
    data = _ops_data(_call("suppliers", "create", [op]))
    assert _op(data, 0)["outcome"] == "rejected"
    assert _op(data, 0)["error"]["code"] == "invalid_request"
    assert not [c for c in gw.calls if c["method"] == "POST"]


def test_create_rejects_identity_fields(access_context, s2s):
    access_context()
    gw = s2s(post=CREATE_PAYLOAD, get=EMPTY_LIST)
    op = {"supplier": {**VALID_CREATE_SUPPLIER, "codusr": "000304"}}
    data = _ops_data(_call("suppliers", "create", [op]))
    assert _op(data, 0)["outcome"] == "rejected"
    assert not [c for c in gw.calls if c["method"] == "POST"]


def test_create_rejects_update_shape(access_context):
    access_context()
    op = {"supplier_code": "000123", "supplier_store": "01", "fields": {}}
    data = _ops_data(_call("suppliers", "create", [op]))
    assert _op(data, 0)["outcome"] == "rejected"


def test_create_duplicate_precheck_rejects(access_context, s2s):
    access_context()
    gw = s2s(post=CREATE_PAYLOAD, get=DUP_LIST)
    op = {"supplier": dict(VALID_CREATE_SUPPLIER)}
    data = _ops_data(_call("suppliers", "create", [op]))
    entry = _op(data, 0)
    assert entry["outcome"] == "rejected"
    assert entry["error"]["code"] == "supplier_duplicate_tax_id"
    assert "00077701" in entry["error"]["message"]
    assert not [c for c in gw.calls if c["method"] == "POST"]


def test_create_precheck_failure_does_not_block(access_context, s2s):
    access_context()
    gw = s2s(
        post=CREATE_PAYLOAD,
        get_error=DelpiApiGatewayError("down", status_code=502),
    )
    op = {"supplier": dict(VALID_CREATE_SUPPLIER)}
    data = _ops_data(_call("suppliers", "create", [op]))
    assert _op(data, 0)["outcome"] == "confirmed"
    assert len([c for c in gw.calls if c["method"] == "POST"]) == 1


# -- update ------------------------------------------------------------------


def test_update_confirmed(access_context, s2s):
    access_context()
    gw = s2s(put=UPDATE_PAYLOAD)
    op = {
        "supplier_code": "000123",
        "supplier_store": "01",
        "fields": {"phone": "1133334444", "email": "a@b.com"},
    }
    data = _ops_data(_call("suppliers", "update", [op]))
    entry = _op(data, 0)
    assert entry["outcome"] == "confirmed"
    assert entry["supplier_id"] == "00012301"
    assert entry["persistence_proven"] is True
    put_calls = [c for c in gw.calls if c["method"] == "PUT"]
    assert put_calls[0]["path"] == "/integrations/protheus/suppliers/00012301"
    assert put_calls[0]["correlation_id"] == data["correlation_id"]


def test_update_requires_identity(access_context, s2s):
    access_context()
    gw = s2s(put=UPDATE_PAYLOAD)
    op = {"fields": {"phone": "1"}}
    data = _ops_data(_call("suppliers", "update", [op]))
    entry = _op(data, 0)
    assert entry["outcome"] == "rejected"
    assert entry["error"]["code"] == "invalid_identity"
    assert not gw.calls


def test_update_rejects_protected_tax_id(access_context, s2s):
    access_context()
    gw = s2s(put=UPDATE_PAYLOAD)
    op = {
        "supplier_code": "1",
        "supplier_store": "1",
        "fields": {"tax_id": "11222333000181"},
    }
    data = _ops_data(_call("suppliers", "update", [op]))
    entry = _op(data, 0)
    assert entry["outcome"] == "rejected"
    assert not gw.calls


def test_update_rejects_unknown_field(access_context, s2s):
    access_context()
    gw = s2s(put=UPDATE_PAYLOAD)
    op = {
        "supplier_code": "1",
        "supplier_store": "1",
        "fields": {"not_a_field": "x"},
    }
    data = _ops_data(_call("suppliers", "update", [op]))
    assert _op(data, 0)["outcome"] == "rejected"
    assert not gw.calls


def test_update_normalizes_identity(access_context, s2s):
    access_context()
    gw = s2s(put=UPDATE_PAYLOAD)
    op = {"supplier_code": "123", "supplier_store": "1", "fields": {"phone": "1"}}
    _ops_data(_call("suppliers", "update", [op]))
    assert gw.calls[0]["path"].endswith("/00012301")


# -- upstream error mapping ---------------------------------------------------


def test_write_disabled_gate_mapped(access_context, s2s):
    access_context()
    s2s(
        error=DelpiApiGatewayError(
            "gated",
            status_code=503,
            code="PROTHEUS_SUPPLIER_CREATE_DISABLED",
        ),
        get=EMPTY_LIST,
    )
    op = {"supplier": dict(VALID_CREATE_SUPPLIER)}
    data = _ops_data(_call("suppliers", "create", [op]))
    entry = _op(data, 0)
    assert entry["outcome"] == "write_disabled"
    assert entry["error"]["code"] == "PROTHEUS_SUPPLIER_CREATE_DISABLED"
    assert entry["http_status"] == 503


def test_transport_failure_is_indeterminate(access_context, s2s):
    access_context()
    s2s(error=DelpiApiGatewayError("api-delpi timeout"), get=EMPTY_LIST)
    op = {"supplier": dict(VALID_CREATE_SUPPLIER)}
    data = _ops_data(_call("suppliers", "create", [op]))
    entry = _op(data, 0)
    assert entry["outcome"] == "indeterminate"
    assert entry["http_status"] == 504


def test_upstream_validation_fields_propagated(access_context, s2s):
    access_context()
    s2s(
        error=DelpiApiGatewayError(
            "client",
            status_code=422,
            code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
            upstream_message="cadastro inválido",
            fields=[{"field": "tax_id", "code": "invalid_value", "message": "bad"}],
        ),
        get=EMPTY_LIST,
    )
    op = {"supplier": dict(VALID_CREATE_SUPPLIER)}
    data = _ops_data(_call("suppliers", "create", [op]))
    entry = _op(data, 0)
    assert entry["outcome"] == "rejected"
    assert entry["error"]["code"] == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"
    assert entry["error"]["fields"][0]["field"] == "tax_id"


def test_upstream_scope_denial_propagated(access_context, s2s):
    access_context()
    s2s(
        error=DelpiApiGatewayError(
            "denied", status_code=403, code="S2S_SCOPE_DENIED"
        ),
    )
    op = {
        "supplier_code": "1",
        "supplier_store": "1",
        "fields": {"phone": "1"},
    }
    data = _ops_data(_call("suppliers", "update", [op]))
    entry = _op(data, 0)
    assert entry["outcome"] == "rejected"
    assert entry["error"]["code"] == "S2S_SCOPE_DENIED"
    assert entry["http_status"] == 403


def test_supplier_not_found_mapped(access_context, s2s):
    access_context()
    s2s(
        error=DelpiApiGatewayError(
            "nf", status_code=404, code="PROTHEUS_SUPPLIER_NOT_FOUND"
        ),
    )
    op = {
        "supplier_code": "999999",
        "supplier_store": "01",
        "fields": {"phone": "1"},
    }
    data = _ops_data(_call("suppliers", "update", [op]))
    entry = _op(data, 0)
    assert entry["outcome"] == "rejected"
    assert entry["error"]["code"] == "PROTHEUS_SUPPLIER_NOT_FOUND"
    assert entry["supplier_id"] == "99999901"


# -- multi-operation + idempotency --------------------------------------------


def test_batch_partial_failure_isolated(access_context, s2s):
    access_context()
    s2s(put=UPDATE_PAYLOAD)
    ops = [
        {"supplier_code": "1", "supplier_store": "1", "fields": {"phone": "1"}},
        {"fields": {"phone": "1"}},  # invalid identity
        {"supplier_code": "2", "supplier_store": "1", "fields": {"email": "a@b.c"}},
    ]
    data = _ops_data(_call("suppliers", "update", ops))
    assert _op(data, 0)["outcome"] == "confirmed"
    assert _op(data, 1)["outcome"] == "rejected"
    assert _op(data, 2)["outcome"] == "confirmed"
    assert data["summary"]["total"] == 3
    assert data["summary"]["confirmed"] == 2
    assert data["summary"]["rejected"] == 1
    assert data["summary"]["total"] == sum(
        v for k, v in data["summary"].items() if k != "total"
    )


def test_idempotent_replay_same_key(access_context, s2s):
    access_context()
    gw = s2s(post=CREATE_PAYLOAD, get=EMPTY_LIST)
    op = {
        "idempotency_key": "order-1",
        "supplier": dict(VALID_CREATE_SUPPLIER),
    }
    first = _ops_data(_call("suppliers", "create", [op]))
    second = _ops_data(_call("suppliers", "create", [op]))
    assert _op(first, 0)["outcome"] == "confirmed"
    replayed = _op(second, 0)
    assert replayed["outcome"] == "replayed"
    assert replayed["replayed_outcome"] == "confirmed"
    assert replayed["operation_id"] == CREATE_PAYLOAD["data"]["operation_id"]
    # exactly one real write across both calls
    assert len([c for c in gw.calls if c["method"] == "POST"]) == 1


def test_idempotent_replay_within_batch(access_context, s2s):
    access_context()
    gw = s2s(post=CREATE_PAYLOAD, get=EMPTY_LIST)
    op = {
        "idempotency_key": "k-dup",
        "supplier": dict(VALID_CREATE_SUPPLIER),
    }
    data = _ops_data(_call("suppliers", "create", [op, op]))
    assert _op(data, 0)["outcome"] == "confirmed"
    assert _op(data, 1)["outcome"] == "replayed"
    assert len([c for c in gw.calls if c["method"] == "POST"]) == 1


def test_idempotency_conflict_on_different_payload(access_context, s2s):
    access_context()
    gw = s2s(post=CREATE_PAYLOAD, get=EMPTY_LIST)
    op1 = {"idempotency_key": "k1", "supplier": dict(VALID_CREATE_SUPPLIER)}
    op2 = {
        "idempotency_key": "k1",
        "supplier": {**VALID_CREATE_SUPPLIER, "supplier_name": "OTHER"},
    }
    _ops_data(_call("suppliers", "create", [op1]))
    data = _ops_data(_call("suppliers", "create", [op2]))
    entry = _op(data, 0)
    assert entry["outcome"] == "rejected"
    assert entry["error"]["code"] == "idempotency_conflict"
    assert len([c for c in gw.calls if c["method"] == "POST"]) == 1


def test_idempotent_replay_survives_process_restart(access_context, s2s, idem_store):
    """Cross-restart dedup: the claim row lives in the durable store —
    simulating a restart (fresh executor, same store) still replays."""
    access_context()
    store = idem_store()
    gw = s2s(post=CREATE_PAYLOAD, get=EMPTY_LIST)
    op = {
        "idempotency_key": "boot-1",
        "supplier": dict(VALID_CREATE_SUPPLIER),
    }
    _ops_data(_call("suppliers", "create", [op]))
    # "restart": a second invocation path shares only the durable store —
    # no in-process replay cache exists anymore.
    second = _ops_data(_call("suppliers", "create", [op]))
    assert _op(second, 0)["outcome"] == "replayed"
    assert _op(second, 0)["replayed_outcome"] == "confirmed"
    assert len([c for c in gw.calls if c["method"] == "POST"]) == 1
    assert store.complete_calls == 1


def test_in_progress_claim_blocks_reexecution(access_context, s2s, idem_store):
    """Concurrent same-key: while the first claim is still 'in_progress'
    the second requester gets an honest in_progress — never a re-write."""
    ns = access_context()
    gw = s2s(post=CREATE_PAYLOAD, get=EMPTY_LIST)
    op = {
        "idempotency_key": "flight-1",
        "supplier": dict(VALID_CREATE_SUPPLIER),
    }
    store = idem_store()
    # Claim the key first without completing — mimics a concurrent caller
    # mid-write or a worker that died after claiming.
    claim = store.claim(
        actor_subject=str(ns.id),
        entity="suppliers",
        action="create",
        idempotency_key="flight-1",
        payload_hash=supplier_execute._payload_hash(op),
        correlation_id="corr",
    )
    assert claim.kind == "claimed"
    data = _ops_data(_call("suppliers", "create", [op]))
    entry = _op(data, 0)
    assert entry["outcome"] == "in_progress"
    assert entry["error"]["code"] == "operation_in_progress"
    assert not [c for c in gw.calls if c["method"] == "POST"]


def test_indeterminate_result_replayed_not_retried(access_context, s2s):
    """A timed-out write is never blindly retried: the indeterminate
    result is persisted on the claim and replayed on retry."""
    access_context()
    gw = s2s(
        error=DelpiApiGatewayError("api-delpi timeout"),
        get=EMPTY_LIST,
    )
    op = {
        "idempotency_key": "timeout-1",
        "supplier": dict(VALID_CREATE_SUPPLIER),
    }
    first = _ops_data(_call("suppliers", "create", [op]))
    assert _op(first, 0)["outcome"] == "indeterminate"
    second = _ops_data(_call("suppliers", "create", [op]))
    entry = _op(second, 0)
    assert entry["outcome"] == "replayed"
    assert entry["replayed_outcome"] == "indeterminate"
    assert len([c for c in gw.calls if c["method"] == "POST"]) == 1


def test_idempotency_store_unavailable_fails_closed(access_context, s2s, idem_store):
    """Keyed write without a working claim store is never issued."""
    access_context()
    gw = s2s(post=CREATE_PAYLOAD, get=EMPTY_LIST)
    idem_store(fail_claim=True)
    op = {
        "idempotency_key": "down-1",
        "supplier": dict(VALID_CREATE_SUPPLIER),
    }
    data = _ops_data(_call("suppliers", "create", [op]))
    entry = _op(data, 0)
    assert entry["outcome"] == "indeterminate"
    assert entry["error"]["code"] == "idempotency_store_unavailable"
    assert entry["http_status"] == 503
    assert not [c for c in gw.calls if c["method"] == "POST"]


def test_unkeyed_operation_bypasses_store(access_context, s2s, idem_store):
    """No idempotency_key → Portal parity: no claim, write proceeds."""
    access_context()
    store = idem_store()
    gw = s2s(post=CREATE_PAYLOAD, get=EMPTY_LIST)
    op = {"supplier": dict(VALID_CREATE_SUPPLIER)}
    data = _ops_data(_call("suppliers", "create", [op]))
    assert _op(data, 0)["outcome"] == "confirmed"
    assert store.claim_calls == 0
    assert len([c for c in gw.calls if c["method"] == "POST"]) == 1


def test_mixed_action_calls_independent(access_context, s2s):
    access_context()
    gw = s2s(post=CREATE_PAYLOAD, put=UPDATE_PAYLOAD, get=EMPTY_LIST)
    create = _ops_data(
        _call(
            "suppliers", "create", [{"supplier": dict(VALID_CREATE_SUPPLIER)}]
        )
    )
    update = _ops_data(
        _call(
            "suppliers",
            "update",
            [
                {
                    "supplier_code": "1",
                    "supplier_store": "1",
                    "fields": {"phone": "1"},
                }
            ],
        )
    )
    assert _op(create, 0)["outcome"] == "confirmed"
    assert _op(update, 0)["outcome"] == "confirmed"
    methods = {c["method"] for c in gw.calls}
    assert {"POST", "PUT"} <= methods


# -- regression: read-only tools unaffected -------------------------------------


def test_catalog_lists_execute_capability(access_context):
    access_context()
    result = tool_bridge.tool_get_context("catalog")
    data = _unwrap(result)["data"]
    names = {t["name"] for t in data["tools"]}
    assert names == {"get_context", "read", "analyze", "knowledge", "execute"}
    execute = data["capabilities"]["execute"]
    assert execute["entities"]["suppliers"]["actions"] == ["create", "update"]
