"""IDENTITY-002 legacy repair — unit tests for repair_glpi_user_names script."""
from __future__ import annotations

import pytest

from scripts import repair_glpi_user_names as repair


def _kc(uid="kc-1", first="Ana", last="Silva", email="ana@x.com", username="ana"):
    return {
        "id": uid,
        "username": username,
        "firstName": first,
        "lastName": last,
        "email": email,
    }


def _glpi(gid=10, first="Ana", last="Silva", name="ana@x.com"):
    return {"id": gid, "name": name, "firstname": first, "realname": last}


# --- build_mappings ---------------------------------------------------------

def test_mapping_a_session_link_wins():
    m = repair.build_mappings(
        [_kc(uid="s1")], [_glpi(gid=7)], linked={"s1": 7}, glpi_emails={}
    )
    assert m["s1"] == {"glpi_id": 7, "via": "session", "ambiguous": False}


def test_mapping_b_unique_email_match():
    m = repair.build_mappings(
        [_kc(uid="s1", email="a@x.com")],
        [_glpi(gid=9)],
        linked={},
        glpi_emails={9: {"a@x.com"}},
    )
    assert m["s1"]["glpi_id"] == 9 and m["s1"]["via"] == "email"


def test_mapping_b_jit_name_is_email_evidence():
    m = repair.build_mappings(
        [_kc(uid="s1", email="jit@x.com")],
        [_glpi(gid=11, name="jit@x.com")],
        linked={},
        glpi_emails={},
    )
    assert m["s1"]["glpi_id"] == 11 and m["s1"]["via"] == "email"


def test_mapping_b_duplicate_glpi_email_is_ambiguous():
    m = repair.build_mappings(
        [_kc(uid="s1", email="dup@x.com")],
        [_glpi(gid=1, name="x"), _glpi(gid=2, name="y")],
        linked={},
        glpi_emails={1: {"dup@x.com"}, 2: {"dup@x.com"}},
    )
    assert m["s1"]["glpi_id"] is None and m["s1"]["ambiguous"] is True


def test_mapping_b_duplicate_keycloak_email_is_ambiguous():
    users = [_kc(uid="s1", email="dup@x.com"), _kc(uid="s2", email="dup@x.com")]
    m = repair.build_mappings(users, [_glpi(gid=1)], linked={}, glpi_emails={1: {"dup@x.com"}})
    assert m["s1"]["ambiguous"] is True and m["s2"]["ambiguous"] is True


def test_mapping_email_case_insensitive():
    m = repair.build_mappings(
        [_kc(uid="s1", email="Ana@X.com")], [_glpi(gid=3, name="x")],
        linked={}, glpi_emails={3: {"ana@x.com"}},
    )
    assert m["s1"]["glpi_id"] == 3


# --- diff / classify --------------------------------------------------------

def test_diff_firstname_only():
    assert repair.diff_user(_kc(first="Ana Maria"), _glpi(first="Ana")) == {
        "firstname": "Ana Maria"
    }


def test_diff_realname_only():
    assert repair.diff_user(_kc(last="Silva Souza"), _glpi(last="Silva")) == {
        "realname": "Silva Souza"
    }


def test_diff_both_fields():
    d = repair.diff_user(_kc(first="José Wigner", last="Quintino Bindacco"),
                         _glpi(first="José", last="Wigner"))
    assert d == {"firstname": "José Wigner", "realname": "Quintino Bindacco"}


def test_diff_legacy_malformed_values():
    d = repair.diff_user(_kc(first="João", last="Silva"), _glpi(first="0", last=""))
    assert d == {"firstname": "João", "realname": "Silva"}


def test_diff_blank_canonical_never_writes():
    assert repair.diff_user(_kc(first="", last=""), _glpi(first="Ana", last="Silva")) == {}


def test_classify_statuses():
    kc = _kc()
    mapping = {"glpi_id": 1, "via": "email", "ambiguous": False}
    assert repair.classify(kc, _glpi(), mapping)[0] == repair.IN_SYNC
    assert repair.classify(kc, _glpi(first="An"), mapping)[0] == repair.DRIFT_FIRSTNAME
    assert repair.classify(kc, _glpi(last="Si"), mapping)[0] == repair.DRIFT_REALNAME
    assert repair.classify(kc, _glpi(first="A", last="S"), mapping)[0] == repair.DRIFT_BOTH
    assert repair.classify(kc, _glpi(first="A", last="S"), mapping, entity_0_only=True)[0] == repair.AUTHORITY_REQUIRED
    assert repair.classify(kc, None, mapping)[0] == repair.UNRESOLVED
    assert repair.classify(kc, _glpi(), {"glpi_id": None, "ambiguous": True})[0] == repair.AMBIGUOUS_MAPPING
    assert repair.classify(kc, _glpi(), {"glpi_id": None, "ambiguous": False})[0] == repair.UNRESOLVED
    assert repair.classify(_kc(first="", last=""), _glpi(), mapping)[0] == repair.MISSING_CANONICAL
    assert repair.classify(None, _glpi(), None)[0] == repair.OUT_OF_SCOPE


# --- glpi_put_user allowlist -------------------------------------------------

def test_put_user_rejects_arbitrary_fields(monkeypatch):
    monkeypatch.setattr(repair, "_request", lambda *a, **k: (200, {}))
    with pytest.raises(ValueError):
        repair.glpi_put_user("b", "app", "sess", 1, {"email": "x@x.com"})
    with pytest.raises(ValueError):
        repair.glpi_put_user("b", "app", "sess", 1, {"firstname": "A", "is_active": 0})


def test_put_user_body_shape(monkeypatch):
    captured = {}

    def fake(method, url, **kw):
        captured.update(kw.get("json_body") or {})
        return 200, {}

    monkeypatch.setattr(repair, "_request", fake)
    repair.glpi_put_user("b", "app", "sess", 5, {"firstname": "Ana"})
    assert captured == {"input": {"firstname": "Ana"}}


# --- apply_candidate ---------------------------------------------------------

def _cand(diff):
    return {"subject": "s1", "glpi_id": 7, "new_values": diff, "status": repair.DRIFT_BOTH}


def test_apply_writes_and_verifies(monkeypatch):
    store = {"firstname": "José", "realname": "Wigner"}
    calls = {"get": 0, "put": 0}

    def fake_get(base, app, sess, path):
        calls["get"] += 1
        return 200, dict(store)

    def fake_put(base, app, sess, uid, fields):
        calls["put"] += 1
        store.update(fields)
        return 200, {}

    monkeypatch.setattr(repair, "glpi_get", fake_get)
    monkeypatch.setattr(repair, "glpi_put_user", fake_put)
    rec = repair.apply_candidate("b", "a", "s", _cand(
        {"firstname": "José Wigner", "realname": "Quintino Bindacco"}))
    assert rec["outcome"] == repair.UPDATED
    assert rec["fields"] == ["firstname", "realname"]
    assert calls["put"] == 1 and calls["get"] == 2


def test_apply_noop_when_already_synced(monkeypatch):
    store = {"firstname": "Ana", "realname": "Silva"}
    monkeypatch.setattr(repair, "glpi_get", lambda *a: (200, dict(store)))
    put = {"n": 0}
    monkeypatch.setattr(repair, "glpi_put_user",
                        lambda *a, **k: put.__setitem__("n", put["n"] + 1) or (200, {}))
    rec = repair.apply_candidate("b", "a", "s", _cand({"firstname": "Ana", "realname": "Silva"}))
    assert rec["outcome"] == repair.NOOP and put["n"] == 0


def test_apply_second_run_zero_writes(monkeypatch):
    """Idempotency: after a successful repair, rerun produces NOOP."""
    store = {"firstname": "José Wigner", "realname": "Quintino Bindacco"}
    monkeypatch.setattr(repair, "glpi_get", lambda *a: (200, dict(store)))
    monkeypatch.setattr(repair, "glpi_put_user", lambda *a, **k: (200, {}))
    rec = repair.apply_candidate("b", "a", "s", _cand(
        {"firstname": "José Wigner", "realname": "Quintino Bindacco"}))
    assert rec["outcome"] == repair.NOOP


def test_apply_forbidden(monkeypatch):
    monkeypatch.setattr(repair, "glpi_get", lambda *a: (200, {"firstname": "X"}))
    monkeypatch.setattr(repair, "glpi_put_user", lambda *a, **k: (403, {}))
    rec = repair.apply_candidate("b", "a", "s", _cand({"firstname": "Y"}))
    assert rec["outcome"] == repair.FAILED_FORBIDDEN


def test_apply_unavailable(monkeypatch):
    monkeypatch.setattr(repair, "glpi_get", lambda *a: (200, {"firstname": "X"}))
    monkeypatch.setattr(repair, "glpi_put_user", lambda *a, **k: (0, None))
    rec = repair.apply_candidate("b", "a", "s", _cand({"firstname": "Y"}))
    assert rec["outcome"] == repair.FAILED_UNAVAILABLE


def test_apply_2xx_reread_mismatch_is_verification_failure(monkeypatch):
    store = {"firstname": "José"}
    monkeypatch.setattr(repair, "glpi_get", lambda *a: (200, dict(store)))
    monkeypatch.setattr(repair, "glpi_put_user", lambda *a, **k: (200, {}))  # write ignored
    rec = repair.apply_candidate("b", "a", "s", _cand({"firstname": "José Wigner"}))
    assert rec["outcome"] == repair.FAILED_VERIFICATION


def test_apply_drops_non_writable_diff_fields(monkeypatch):
    store = {"firstname": "Ana", "realname": "Silva"}
    monkeypatch.setattr(repair, "glpi_get", lambda *a: (200, dict(store)))
    rec = repair.apply_candidate("b", "a", "s",
                                 _cand({"firstname": "Ana", "email": "evil@x.com"}))
    assert rec["outcome"] == repair.NOOP


def test_audit_record_has_no_name_values(monkeypatch):
    store = {"firstname": "José", "realname": "Wigner"}
    monkeypatch.setattr(repair, "glpi_get", lambda *a: (200, dict(store)))

    def fake_put(base, app, sess, uid, fields):
        store.update(fields)
        return 200, {}

    monkeypatch.setattr(repair, "glpi_put_user", fake_put)
    rec = repair.apply_candidate("b", "a", "s", _cand({"firstname": "José Wigner"}))
    import json
    assert "Wigner" not in json.dumps(rec) and "José" not in json.dumps(rec)


# --- build_plan counts --------------------------------------------------------

def test_build_plan_counts():
    kc = [
        _kc(uid="s1", email="a@x.com"),
        _kc(uid="s2", email="b@x.com", first="B B", last="L L", username="b"),
        _kc(uid="s3", email="dup@x.com", username="c"),
        _kc(uid="s4", email="dup@x.com", username="d"),
    ]
    g = [
        _glpi(gid=1, name="a@x.com"),
        _glpi(gid=2, name="b@x.com", first="B", last="L"),
        _glpi(gid=3, name="dup@x.com"),
    ]
    entities = {1: {1}, 2: {1}, 3: {0}}
    mappings = repair.build_mappings(kc, g, linked={"s1": 1}, glpi_emails={
        1: {"a@x.com"}, 2: {"b@x.com"}, 3: {"dup@x.com"}})
    plan = repair.build_plan(kc, g, mappings, entities)
    c = plan.counts
    assert c["keycloak_users"] == 4 and c["glpi_users"] == 3
    assert c["in_sync"] == 1 and c["drift_both"] == 1
    assert c["ambiguous"] == 2 and c["glpi_unmapped"] == 1
