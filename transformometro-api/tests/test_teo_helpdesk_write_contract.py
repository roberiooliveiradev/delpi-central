"""BFF → TÉO gateway write-result contract tests.

Covers the canonical result classes at the HTTP boundary:

- executed + verified write (201 upload / 200 decision) → body;
- executed + unconfirmed write (HTTP 207) → governed partial body,
  returned to the caller with persisted identifiers — never flattened
  into success nor dropped into a generic error;
- rejected operation (4xx) → typed ``GptActionsError``;
- transport failure/timeout → ``upstream_unavailable``;
- contract violation (207 without typed ``outcome``) → normalized to
  ``outcome="untyped_partial"`` with ``contract_violation=True`` — the
  governed layer consumes the proposal and preserves persisted ids for
  reconciliation rather than leaving a replayable proposal behind;
- idempotent replay — same proposal-bound key forwarded, same governed
  result returned by the BFF replay store.

Uses the same ``mod.httpx.Client`` monkeypatch seam as
``test_teo_helpdesk_read.py`` — no real HTTP.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

import tm_app.infrastructure.gateways.helpdesk_bff_gateway as mod
from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.infrastructure.gateways.helpdesk_bff_gateway import (
    HelpdeskBffGateway,
)


# --------------------------------------------------------------------------
# HTTP seam
# --------------------------------------------------------------------------


class _Resp:
    def __init__(self, status: int, body: Any = None) -> None:
        self.status_code = status
        self._body = body if body is not None else {}
        self.headers: dict[str, str] = {}
        self.content = b""

    def json(self) -> Any:
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


class _FakeHttp:
    """Records requests; returns queued responses or raises."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.responses: list[Any] = []

    def queue(self, *responses: Any) -> None:
        self.responses.extend(responses)

    def _next(self) -> Any:
        assert self.responses, "unexpected HTTP call"
        nxt = self.responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt

    def request(self, method, url, json=None, headers=None):
        self.calls.append((method, url, dict(headers or {})))
        return self._next()

    def post(self, url, files=None, data=None, headers=None):
        self.calls.append(("POST", url, dict(headers or {})))
        return self._next()

    def get(self, url, params=None, headers=None):
        self.calls.append(("GET", url, dict(headers or {})))
        return self._next()


@pytest.fixture
def http(monkeypatch: pytest.MonkeyPatch) -> _FakeHttp:
    fake = _FakeHttp()

    class _Client:
        def __init__(self, **_: Any) -> None:
            pass

        def __enter__(self) -> _FakeHttp:
            return fake

        def __exit__(self, *a: Any) -> None:
            return None

    monkeypatch.setattr(mod.httpx, "Client", _Client)
    return fake


@pytest.fixture
def gw() -> HelpdeskBffGateway:
    return HelpdeskBffGateway()


_AUTH = "Bearer user-jwt"
_KEY = "idem-proposal-1"


# --------------------------------------------------------------------------
# Executed writes — verified
# --------------------------------------------------------------------------


def test_upload_201_verified_returns_body(gw, http):
    http.queue(
        _Resp(
            201,
            {
                "document_id": 1460,
                "filename": "e2e.png",
                "mime": "image/png",
                "author_state": "verified",
                "author_verified": True,
                "outcome": "verified",
            },
        )
    )
    out = gw.upload_attachment(
        _AUTH,
        500,
        filename="e2e.png",
        content=b"\x89PNG",
        mime="image/png",
        title=None,
        idempotency_key=_KEY,
    )
    assert out["document_id"] == 1460
    assert out["outcome"] == "verified"
    _, url, headers = http.calls[0]
    assert url.endswith("/tickets/500/attachments")
    assert headers["Idempotency-Key"] == _KEY
    assert headers["Authorization"] == _AUTH


def test_decide_solution_200_verified_returns_body(gw, http):
    http.queue(
        _Resp(
            200,
            {
                "id": 500,
                "status_id": 6,
                "followup_id": 812,
                "outcome": "verified",
                "author_verified": True,
                "status_verified": True,
            },
        )
    )
    out = gw.decide_solution(
        _AUTH, 500, decision="accept", content="ok", idempotency_key=_KEY
    )
    assert out["status_id"] == 6
    assert out["followup_id"] == 812
    method, url, _ = http.calls[0]
    assert method == "POST" and url.endswith("/tickets/500/solution/accept")


# --------------------------------------------------------------------------
# Executed writes — governed partial (HTTP 207)
# --------------------------------------------------------------------------


def test_upload_207_partial_returns_body_with_document_id(gw, http):
    """207 is a governed result, not an error: the caller receives the
    persisted document_id plus the typed outcome for reconciliation."""
    http.queue(
        _Resp(
            207,
            {
                "document_id": 1461,
                "filename": "e2e.png",
                "mime": "image/png",
                "author_state": "unverified",
                "author_verified": False,
                "outcome": "verification_failed",
            },
        )
    )
    out = gw.upload_attachment(
        _AUTH,
        500,
        filename="e2e.png",
        content=b"\x89PNG",
        mime="image/png",
        title=None,
        idempotency_key=_KEY,
    )
    assert out["outcome"] == "verification_failed"
    assert out["author_verified"] is False
    assert out["document_id"] == 1461


def test_decide_solution_207_partial_returns_body_with_followup_id(gw, http):
    for outcome in ("author_mismatch", "author_unverified", "status_unverified"):
        http.queue(
            _Resp(
                207,
                {
                    "id": 500,
                    "status_id": 6,
                    "followup_id": 813,
                    "outcome": outcome,
                    "author_verified": outcome != "author_unverified",
                    "status_verified": outcome != "status_unverified",
                },
            )
        )
        out = gw.decide_solution(
            _AUTH,
            500,
            decision="accept",
            content="ok",
            idempotency_key=_KEY,
        )
        assert out["outcome"] == outcome
        assert out["followup_id"] == 813


def test_207_without_typed_outcome_normalized_to_untyped_partial(gw, http):
    """A 207 missing ``outcome`` violates the contract, but the status
    still means "executed, not fully verified" — a write may have
    persisted. It is normalized to ``untyped_partial`` so the governed
    layer consumes the proposal and surfaces the persisted identifiers
    for reconciliation instead of leaving a reusable proposal behind."""
    http.queue(_Resp(207, {"document_id": 1462}))
    out = gw.upload_attachment(
        _AUTH,
        500,
        filename="e2e.png",
        content=b"\x89PNG",
        mime="image/png",
        title=None,
        idempotency_key=_KEY,
    )
    assert out["outcome"] == "untyped_partial"
    assert out["contract_violation"] is True
    assert out["document_id"] == 1462


# --------------------------------------------------------------------------
# Rejected operation vs transport failure
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "status,error_kind",
    [(400, "validation"), (403, "forbidden"), (409, "conflict"),
     (422, "validation")],
)
def test_rejected_operation_maps_typed_error(gw, http, status, error_kind):
    http.queue(_Resp(status, {"error": "some_code"}))
    with pytest.raises(GptActionsError) as exc:
        gw.decide_solution(
            _AUTH, 500, decision="accept", content="x",
            idempotency_key=_KEY,
        )
    assert exc.value.status_code == status
    assert exc.value.data["error_kind"] == error_kind


def test_idempotency_in_flight_forwards_reconciliation_metadata(gw, http):
    """BFF 409 idempotency_in_flight = a prior execution under this key
    may have persisted. The typed code plus claim metadata must reach
    the caller — retry is blocked until authoritative reconciliation."""
    http.queue(
        _Resp(
            409,
            {
                "error": "idempotency_in_flight",
                "claimed_at": "2026-10-28T12:00:00+00:00",
                "intent": {"ticket_id": 500, "filename": "e2e.png"},
            },
        )
    )
    with pytest.raises(GptActionsError) as exc:
        gw.upload_attachment(
            _AUTH,
            500,
            filename="e2e.png",
            content=b"\x89PNG",
            mime="image/png",
            title=None,
            idempotency_key=_KEY,
        )
    assert exc.value.status_code == 409
    assert exc.value.data["error_code"] == "idempotency_in_flight"
    assert exc.value.data["intent"]["filename"] == "e2e.png"
    assert exc.value.data["claimed_at"] is not None


def test_transport_failure_maps_upstream_unavailable(gw, http):
    http.queue(httpx.ConnectTimeout("timeout"))
    with pytest.raises(GptActionsError) as exc:
        gw.upload_attachment(
            _AUTH,
            500,
            filename="e2e.png",
            content=b"\x89PNG",
            mime="image/png",
            title=None,
            idempotency_key=_KEY,
        )
    assert exc.value.status_code == 502
    assert exc.value.data["error_kind"] == "upstream_unavailable"


# --------------------------------------------------------------------------
# Idempotent replay — same key, same governed result
# --------------------------------------------------------------------------


def test_idempotent_replay_returns_same_partial_result(gw, http):
    """Retrying under the same proposal-bound key replays the stored
    governed response — same document_id, no second side effect."""
    partial = _Resp(
        207,
        {
            "document_id": 1461,
            "filename": "e2e.png",
            "outcome": "verification_failed",
            "author_verified": False,
        },
    )
    http.queue(partial, partial)
    first = gw.upload_attachment(
        _AUTH, 500, filename="e2e.png", content=b"x", mime="image/png",
        title=None, idempotency_key=_KEY,
    )
    second = gw.upload_attachment(
        _AUTH, 500, filename="e2e.png", content=b"x", mime="image/png",
        title=None, idempotency_key=_KEY,
    )
    assert first == second
    assert first["document_id"] == 1461
    keys = [c[2]["Idempotency-Key"] for c in http.calls]
    assert keys == [_KEY, _KEY]
