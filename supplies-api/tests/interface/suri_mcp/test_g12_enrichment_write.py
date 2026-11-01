"""SURI-MCP V13 G12 — enrichment governed write dispatch."""
from unittest.mock import MagicMock, patch
import pytest
from app.interfaces.mcp import tool_bridge, enrichment_execute


class _User:
    is_superadmin = True
    access_token = "tok"
    id = "actor-1"

    def has_permission(self, code):
        return True


def _ok(r):
    return getattr(r, "is_error", getattr(r, "isError", False)) is False


class _Review:
    review_id = "rev-1"
    status = "in_review"


@pytest.fixture
def env():
    svc = MagicMock()
    svc.create_review.return_value = (_Review(), [1, 2])
    svc.decide.return_value = (_Review(), [1], False)
    svc.decide_bulk.return_value = (_Review(), [1, 2], False)
    svc.prepare_update.return_value = (_Review(), [1])
    rl = MagicMock()
    with patch.object(enrichment_execute, "_service", lambda: svc), \
         patch.object(enrichment_execute, "_claim_or_replay",
                      lambda *a, **k: (None, None)), \
         patch.object(enrichment_execute, "registry_rate_limiter",
                      return_value=rl), \
         patch.object(enrichment_execute, "normalize_supplier_id",
                      return_value="12345601"), \
         patch.object(tool_bridge, "_effective_user", return_value=_User()):
        yield svc, rl


def test_review_create_confirmed(env):
    svc, rl = env
    r = tool_bridge.tool_execute(
        "enrichment", "review_create",
        [{"supplier_code": "123456", "supplier_store": "01"}])
    assert _ok(r), r
    svc.create_review.assert_called_once()
    rl.acquire.assert_called_once()
    kw = svc.create_review.call_args.kwargs
    assert kw["supplier_code"] == "123456"


def test_decide_confirmed(env):
    svc, _ = env
    r = tool_bridge.tool_execute(
        "enrichment", "decide",
        [{"supplier_code": "123456", "supplier_store": "01",
          "review_id": "rev-1", "field_key": "trade_name",
          "decision": "ACCEPT", "expected_revision": 3,
          "idempotency_key": "k1"}])
    assert _ok(r), r
    kw = svc.decide.call_args.kwargs
    assert kw["review_id"] == "rev-1" and kw["expected_revision"] == 3


def test_decide_bulk_confirmed(env):
    svc, _ = env
    r = tool_bridge.tool_execute(
        "enrichment", "decide_bulk",
        [{"supplier_code": "123456", "supplier_store": "01",
          "review_id": "rev-1", "field_keys": ["a", "b"],
          "decision": "REJECT", "expected_revision": 3,
          "idempotency_key": "k2"}])
    assert _ok(r), r
    kw = svc.decide_bulk.call_args.kwargs
    assert kw["field_keys"] == ["a", "b"]


def test_prepare_update_confirmed(env):
    svc, _ = env
    r = tool_bridge.tool_execute(
        "enrichment", "prepare_update",
        [{"supplier_code": "123456", "supplier_store": "01",
          "review_id": "rev-1", "expected_revision": 5}])
    assert _ok(r), r
    kw = svc.prepare_update.call_args.kwargs
    assert kw["expected_revision"] == 5


def test_enrichment_unknown_action(env):
    r = tool_bridge.tool_execute(
        "enrichment", "delete", [{"supplier_code": "x"}])
    assert not _ok(r)


def test_decide_rejects_wrong_key(env):
    r = tool_bridge.tool_execute(
        "enrichment", "decide",
        [{"supplier_code": "123456", "supplier_store": "01",
          "review_id": "rev-1", "field_key": "f",
          "decision": "ACCEPT", "expected_revision": 1,
          "bogus": 1}])
    assert not _ok(r)


def test_decide_rejects_bad_decision(env):
    r = tool_bridge.tool_execute(
        "enrichment", "decide",
        [{"supplier_code": "123456", "supplier_store": "01",
          "review_id": "rev-1", "field_key": "f",
          "decision": "MAYBE", "expected_revision": 1}])
    t = str(getattr(r, "content", r))
    assert "MAYBE" in t or "decision" in t
