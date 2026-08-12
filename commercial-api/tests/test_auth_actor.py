"""ContextVar do ator autenticado (notify de carteira)."""

from __future__ import annotations

from types import SimpleNamespace

from commercial_app.core.auth_actor import (
    actor_display_name_from_request,
    bind_request_actor,
    peek_actor_client_id,
    peek_actor_display_name,
)


class _FakeRequest:
    def __init__(self, user: dict | None, client_id: str | None = None) -> None:
        self.state = SimpleNamespace(user=user)
        self.headers = {"X-Client-Id": client_id} if client_id else {}


def test_actor_display_name_prefers_name() -> None:
    request = _FakeRequest(
        {"name": "Maria Souza", "preferred_username": "maria", "sub": "u-42"}
    )
    assert actor_display_name_from_request(request) == "Maria Souza"


def test_actor_display_name_skips_uuid_name() -> None:
    request = _FakeRequest(
        {
            "name": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
            "preferred_username": "vendas.sp",
            "sub": "sub-1",
        }
    )
    assert actor_display_name_from_request(request) == "vendas.sp"


def test_bind_request_actor_sets_display_and_client(monkeypatch) -> None:
    monkeypatch.setattr(
        "commercial_app.interface.http.client_id.client_id_from_request",
        lambda _request: "client-xyz",
    )
    request = _FakeRequest(
        {"name": "Maria Souza", "preferred_username": "maria", "sub": "u-42"}
    )
    with bind_request_actor(request):
        assert peek_actor_display_name() == "Maria Souza"
        assert peek_actor_client_id() == "client-xyz"
    assert peek_actor_display_name() is None
    assert peek_actor_client_id() is None


def test_bind_falls_back_to_username(monkeypatch) -> None:
    monkeypatch.setattr(
        "commercial_app.interface.http.client_id.client_id_from_request",
        lambda _request: None,
    )
    request = _FakeRequest({"preferred_username": "vendas.sp", "sub": "sub-1"})
    with bind_request_actor(request):
        assert peek_actor_display_name() == "vendas.sp"
    assert peek_actor_display_name() is None
