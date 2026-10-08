"""Workspace context: contract bounds, TTL/freshness, resolution statuses."""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.application.workspace_context.workspace_context_contract import (
    WorkspaceContextValidationError,
    parse_workspace_context_payload,
)
from app.application.workspace_context.workspace_context_service import (
    WorkspaceContextService,
)
from app.application.workspace_context.workspace_context_store import (
    WorkspaceContextEntry,
    WorkspaceContextStore,
    _utcnow,
)


def _payload(**over):
    base = {
        "version": 1,
        "app_id": "transformometro",
        "client_instance_id": "tab-1",
        "route_id": "process-workspace",
        "entity_refs": [
            {"entity_type": "process", "entity_id": "P"},
            {"entity_type": "instance", "entity_id": "I"},
            {"entity_type": "revision", "entity_id": "R"},
        ],
        "presentation_state": {"area": "resultados"},
        "canonical_path": "/apps/transformometro/processes/P/instances/I/revisions/R#resultados",
        "active": True,
        "focused": True,
    }
    base.update(over)
    return parse_workspace_context_payload(base)


def _service(ttl=300):
    return WorkspaceContextService(store=WorkspaceContextStore(ttl_seconds=ttl))


# ---------------------------------------------------------------- contract


def test_valid_payload_parses() -> None:
    payload = _payload()
    assert payload.app_id == "transformometro"
    assert payload.client_instance_id == "tab-1"
    assert len(payload.entity_refs) == 3
    assert payload.presentation_state == {"area": "resultados"}


def test_rejects_unknown_keys_and_bad_version() -> None:
    with pytest.raises(WorkspaceContextValidationError):
        _payload(extra_key="x")
    with pytest.raises(WorkspaceContextValidationError):
        _payload(version=2)
    with pytest.raises(WorkspaceContextValidationError):
        _payload(app_id=None)
    with pytest.raises(WorkspaceContextValidationError):
        _payload(client_instance_id="")


def test_rejects_credential_like_keys() -> None:
    with pytest.raises(WorkspaceContextValidationError, match="credential"):
        _payload(presentation_state={"access_token": "abc"})


def test_rejects_unbounded_refs_and_strings() -> None:
    with pytest.raises(WorkspaceContextValidationError):
        _payload(entity_refs=[
            {"entity_type": "t", "entity_id": str(i)} for i in range(5)
        ])
    with pytest.raises(WorkspaceContextValidationError):
        _payload(canonical_path="x" * 501)
    with pytest.raises(WorkspaceContextValidationError):
        _payload(entity_refs=[{"entity_type": "process"}])  # missing id


# --------------------------------------------------------------- resolution


def test_absent_when_nothing_published() -> None:
    svc = _service()
    assert svc.resolve(user_id="u1")["status"] == "absent"


def test_active_single_publisher() -> None:
    svc = _service()
    svc.publish(user_id="u1", payload=_payload())
    out = svc.resolve(user_id="u1", app_id="transformometro")
    assert out["status"] == "active"
    ctx = out["context"]
    assert ctx["entity_refs"][0]["entity_id"] == "P"
    assert ctx["presentation_state"]["area"] == "resultados"
    assert ctx["age_seconds"] >= 0


def test_user_isolation() -> None:
    svc = _service()
    svc.publish(user_id="u1", payload=_payload())
    assert svc.resolve(user_id="u2")["status"] == "absent"


def test_app_isolation() -> None:
    svc = _service()
    svc.publish(user_id="u1", payload=_payload())
    assert svc.resolve(user_id="u1", app_id="tv-dashboard")["status"] == "absent"
    assert svc.resolve(user_id="u1", app_id="transformometro")["status"] == "active"


def test_second_tab_overwrites_same_client_not_others() -> None:
    svc = _service()
    svc.publish(user_id="u1", payload=_payload())
    svc.publish(user_id="u1", payload=_payload(client_instance_id="tab-2", focused=False))
    # Two active entries, one focused -> focused wins.
    out = svc.resolve(user_id="u1")
    assert out["status"] == "active"
    assert out["context"]["client_instance_id"] == "tab-1"


def test_same_material_context_in_two_tabs_is_not_ambiguous() -> None:
    # Technical multiplicity != material ambiguity: two tabs publishing the
    # same app/entity/area context must collapse to one candidate.
    svc = _service()
    svc.publish(user_id="u1", payload=_payload(focused=False))
    svc.publish(user_id="u1", payload=_payload(client_instance_id="tab-2", focused=False))
    out = svc.resolve(user_id="u1")
    assert out["status"] == "active"
    assert out["context"]["entity_refs"][0]["entity_id"] == "P"


def test_home_never_competes_with_material_process_context() -> None:
    svc = _service()
    svc.publish(
        user_id="u1",
        payload=_payload(
            client_instance_id="tab-home",
            route_id="home",
            entity_refs=[],
            presentation_state={},
            canonical_path="/apps/transformometro",
            focused=False,
        ),
    )
    svc.publish(
        user_id="u1",
        payload=_payload(
            client_instance_id="tab-p",
            entity_refs=[{"entity_type": "process", "entity_id": "P"}],
            presentation_state={"area": "visao-geral"},
            focused=False,
        ),
    )
    out = svc.resolve(user_id="u1")
    assert out["status"] == "active"
    assert out["context"]["entity_refs"][0]["entity_id"] == "P"


def test_home_is_active_when_it_is_the_only_context() -> None:
    svc = _service()
    svc.publish(
        user_id="u1",
        payload=_payload(
            route_id="home",
            entity_refs=[],
            presentation_state={},
            canonical_path="/apps/transformometro",
        ),
    )
    out = svc.resolve(user_id="u1")
    assert out["status"] == "active"
    assert out["context"]["route_id"] == "home"


def test_distinct_processes_stay_ambiguous() -> None:
    svc = _service()
    svc.publish(
        user_id="u1",
        payload=_payload(
            entity_refs=[{"entity_type": "process", "entity_id": "P"}],
            presentation_state={"area": "visao-geral"},
            focused=False,
        ),
    )
    svc.publish(
        user_id="u1",
        payload=_payload(
            client_instance_id="tab-2",
            entity_refs=[{"entity_type": "process", "entity_id": "Q"}],
            presentation_state={"area": "visao-geral"},
            focused=False,
        ),
    )
    out = svc.resolve(user_id="u1")
    assert out["status"] == "ambiguous"
    assert len(out["candidates"]) == 2


def test_more_specific_context_wins_same_material_chain() -> None:
    # process P + process P / instance I -> the deeper context wins.
    svc = _service()
    svc.publish(
        user_id="u1",
        payload=_payload(
            entity_refs=[{"entity_type": "process", "entity_id": "P"}],
            presentation_state={"area": "visao-geral"},
            focused=False,
        ),
    )
    svc.publish(
        user_id="u1",
        payload=_payload(
            client_instance_id="tab-2",
            entity_refs=[
                {"entity_type": "process", "entity_id": "P"},
                {"entity_type": "instance", "entity_id": "I"},
            ],
            presentation_state={"area": "resultados"},
            focused=False,
        ),
    )
    out = svc.resolve(user_id="u1")
    assert out["status"] == "active"
    assert out["context"]["entity_refs"][1]["entity_id"] == "I"


def test_specificity_never_crosses_incompatible_chains() -> None:
    # P/I vs P/J: same process, different instances -> ambiguous.
    svc = _service()
    svc.publish(
        user_id="u1",
        payload=_payload(
            entity_refs=[
                {"entity_type": "process", "entity_id": "P"},
                {"entity_type": "instance", "entity_id": "I"},
            ],
            focused=False,
        ),
    )
    svc.publish(
        user_id="u1",
        payload=_payload(
            client_instance_id="tab-2",
            entity_refs=[
                {"entity_type": "process", "entity_id": "P"},
                {"entity_type": "instance", "entity_id": "J"},
            ],
            focused=False,
        ),
    )
    out = svc.resolve(user_id="u1")
    assert out["status"] == "ambiguous"


def test_same_process_different_area_is_materially_distinct() -> None:
    # Same entity chain but different presentation (area) -> distinct
    # candidates; without focus evidence this is a real ambiguity.
    svc = _service()
    svc.publish(
        user_id="u1",
        payload=_payload(
            entity_refs=[{"entity_type": "process", "entity_id": "P"}],
            presentation_state={"area": "visao-geral"},
            focused=False,
        ),
    )
    svc.publish(
        user_id="u1",
        payload=_payload(
            client_instance_id="tab-2",
            entity_refs=[{"entity_type": "process", "entity_id": "P"}],
            presentation_state={"area": "documentacao"},
            focused=False,
        ),
    )
    out = svc.resolve(user_id="u1")
    assert out["status"] == "ambiguous"


def test_focused_resolves_material_tiebreak_not_recency() -> None:
    # Two distinct materials; exactly one focused -> focused wins.
    svc = _service()
    svc.publish(
        user_id="u1",
        payload=_payload(
            entity_refs=[{"entity_type": "process", "entity_id": "P"}],
            presentation_state={"area": "visao-geral"},
            focused=False,
        ),
    )
    svc.publish(
        user_id="u1",
        payload=_payload(
            client_instance_id="tab-2",
            entity_refs=[{"entity_type": "process", "entity_id": "Q"}],
            presentation_state={"area": "visao-geral"},
            focused=True,
        ),
    )
    out = svc.resolve(user_id="u1")
    assert out["status"] == "active"
    assert out["context"]["entity_refs"][0]["entity_id"] == "Q"


def test_stale_when_expired(tmp_path) -> None:
    svc = _service(ttl=60)
    store = svc._store
    svc.publish(user_id="u1", payload=_payload())
    # Force expiry by rewriting the entry timestamps.
    key = ("u1", "tab-1")
    old = store._entries[key]
    store._entries[key] = WorkspaceContextEntry(
        user_id=old.user_id,
        payload=old.payload,
        updated_at=old.updated_at - timedelta(seconds=90),
        expires_at=old.expires_at - timedelta(seconds=90),
    )
    out = svc.resolve(user_id="u1")
    assert out["status"] == "stale"
    assert out["context"]["entity_refs"][0]["entity_id"] == "P"


def test_explicit_deactivate_yields_absent() -> None:
    svc = _service()
    svc.publish(user_id="u1", payload=_payload(active=False))
    out = svc.resolve(user_id="u1")
    assert out["status"] == "absent"


def test_unpublish_removes_entry() -> None:
    svc = _service()
    svc.publish(user_id="u1", payload=_payload())
    assert svc.unpublish(user_id="u1", client_instance_id="tab-1")["status"] == "removed"
    assert svc.resolve(user_id="u1")["status"] == "absent"


def test_payload_never_grants_authority() -> None:
    # Structural guarantee: the contract has no permission/scope fields —
    # unknown keys are rejected, so nothing AuthZ-shaped can be smuggled in.
    payload = _payload()
    assert "permissions" not in payload.as_dict()
    assert "roles" not in payload.as_dict()



# --------------------------------------------------------------- redis store


class _FakePipeline:
    def __init__(self, client):
        self._client = client
        self._ops = []

    def setex(self, key, ttl, value):
        self._ops.append(("setex", key, ttl, value))
        return self

    def sadd(self, key, *members):
        self._ops.append(("sadd", key, members))
        return self

    def expire(self, key, ttl):
        self._ops.append(("expire", key, ttl))
        return self

    def delete(self, key):
        self._ops.append(("delete", key))
        return self

    def srem(self, key, *members):
        self._ops.append(("srem", key, members))
        return self

    def execute(self):
        results = []
        for op in self._ops:
            results.append(self._client._apply(op))
        self._ops = []
        return results


class _FakeRedis:
    def __init__(self):
        self._kv = {}
        self._sets = {}

    def pipeline(self):
        return _FakePipeline(self)

    def _apply(self, op):
        name = op[0]
        if name == "setex":
            self._kv[op[1]] = op[3]
            return True
        if name == "sadd":
            self._sets.setdefault(op[1], set()).update(op[2])
            return True
        if name == "expire":
            return True
        if name == "delete":
            return int(self._kv.pop(op[1], None) is not None)
        if name == "srem":
            self._sets.get(op[1], set()).difference_update(op[2])
            return True
        return None

    def smembers(self, key):
        return set(self._sets.get(key, set()))

    def mget(self, keys):
        return [self._kv.get(k) for k in keys]

    def srem(self, key, *members):
        self._sets.get(key, set()).difference_update(members)


def _redis_store(monkeypatch):
    import sys
    import types

    fake = _FakeRedis()
    module = types.ModuleType("redis")
    module.from_url = lambda url, decode_responses=True: fake
    monkeypatch.setitem(sys.modules, "redis", module)
    from app.infrastructure.workspace_context.redis_workspace_context_store import (
        RedisWorkspaceContextStore,
    )

    return (
        RedisWorkspaceContextStore(redis_url="redis://fake:6379/0", ttl_seconds=300),
        fake,
    )


def test_redis_store_roundtrip_and_delete(monkeypatch) -> None:
    store, fake = _redis_store(monkeypatch)
    store.put(user_id="u1", payload=_payload())
    store.put(user_id="u1", payload=_payload(client_instance_id="tab-2", focused=False))

    entries = store.list_for_user(user_id="u1")
    assert len(entries) == 2
    assert {e.payload.client_instance_id for e in entries} == {"tab-1", "tab-2"}
    refs = entries[0].payload.entity_refs
    assert [(r.entity_type, r.entity_id) for r in refs] == [
        ("process", "P"),
        ("instance", "I"),
        ("revision", "R"),
    ]
    assert store.list_for_user(user_id="other") == []

    assert store.delete(user_id="u1", client_instance_id="tab-2") is True
    remaining = store.list_for_user(user_id="u1")
    assert [e.payload.client_instance_id for e in remaining] == ["tab-1"]
    assert fake.smembers("wctx:user:u1") == {"tab-1"}


def test_redis_store_fresh_only_respects_expires_at(monkeypatch) -> None:
    store, fake = _redis_store(monkeypatch)
    store.put(user_id="u1", payload=_payload())
    key = "wctx:entry:u1:tab-1"
    import json

    doc = json.loads(fake._kv[key])
    doc["expires_at"] = (_utcnow() - timedelta(seconds=1)).isoformat()
    fake._kv[key] = json.dumps(doc)

    assert store.list_for_user(user_id="u1", fresh_only=True) == []
    stale = store.list_for_user(user_id="u1", fresh_only=False)
    assert len(stale) == 1 and stale[0].expires_at < _utcnow()
