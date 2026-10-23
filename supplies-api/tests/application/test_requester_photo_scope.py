"""RequesterPhotoScopeGuard — membership against the authorized facet."""

from __future__ import annotations

from app.application.services.requester_photo_scope import (
    RequesterPhotoScopeGuard,
)


class FakeGateway:
    def __init__(self, items=None, fail=False):
        self._items = items or []
        self.fail = fail
        self.calls: list[str | None] = []

    def list_requesters(self, *, access_token, params=None, query_string=None):
        self.calls.append(query_string)
        if self.fail:
            raise RuntimeError("owner down")
        return {"data": {"items": list(self._items)}}


def _guard(items=None, fail=False):
    return RequesterPhotoScopeGuard(
        gateway=FakeGateway(items=items, fail=fail)
    )


def test_allowed_when_requester_in_authorized_facet():
    guard = _guard(items=[{"protheus_user_id": "000304"}])
    assert guard.is_allowed(
        protheus_user_id="000304",
        access_token="tok",
        facet_query="branch=01",
    )


def test_denied_when_requester_outside_facet():
    """Positive sibling: same route, id absent from the scoped facet."""
    guard = _guard(items=[{"protheus_user_id": "000304"}])
    assert not guard.is_allowed(
        protheus_user_id="000999",
        access_token="tok",
        facet_query="branch=01",
    )


def test_denied_when_facet_lookup_fails():
    guard = _guard(fail=True)
    assert not guard.is_allowed(
        protheus_user_id="000304",
        access_token="tok",
        facet_query="branch=01",
    )


def test_denied_blank_id_or_token():
    guard = _guard(items=[{"protheus_user_id": "000304"}])
    assert not guard.is_allowed(
        protheus_user_id="", access_token="tok", facet_query="branch=01"
    )
    assert not guard.is_allowed(
        protheus_user_id="000304", access_token="", facet_query="branch=01"
    )


def test_facet_cached_per_caller_and_query():
    gateway = FakeGateway(items=[{"protheus_user_id": "000304"}])
    guard = RequesterPhotoScopeGuard(gateway=gateway)
    for _ in range(3):
        guard.is_allowed(
            protheus_user_id="000304",
            access_token="tok",
            facet_query="branch=01",
        )
    assert gateway.calls == ["branch=01"]
    guard.is_allowed(
        protheus_user_id="000304",
        access_token="tok",
        facet_query="branch=02",
    )
    assert gateway.calls == ["branch=01", "branch=02"]
