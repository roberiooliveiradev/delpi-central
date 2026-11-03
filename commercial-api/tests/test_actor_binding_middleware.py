"""Regressão: vínculo de ator via middleware http (contexto da requisição).

Incidente 03/11/2026 — a dependência sync com `yield` que chamava
`bind_request_actor` quebrava com `ValueError: Token was created in a
different Context` (enter/exit em contextos distintos), derrubando todas as
rotas /seller-portfolios/* com HTTP 500. O vínculo agora ocorre em middleware
que roda após o jwt_middleware; ContextVar nunca cruza contextos.
"""
from __future__ import annotations

import asyncio
import contextvars

from starlette.requests import Request

from commercial_app.core.auth_actor import (
    actor_display_name_from_request,
    bind_request_actor,
    peek_actor_client_id,
    peek_actor_display_name,
)
from commercial_app.middleware.actor_middleware import actor_binding_middleware


def _request(
    path: str = "/seller-portfolios",
    *,
    root_path: str = "",
    user=None,
    client_id: str | None = None,
) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if client_id:
        headers.append((b"x-commercial-client-id", client_id.encode()))
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "root_path": root_path,
        "headers": headers,
        "query_string": b"",
    }
    req = Request(scope)
    req.state.user = user
    return req


def test_bind_request_actor_sets_vars_in_current_context() -> None:
    req = _request(user={"name": "Maria Silva"}, client_id="mfe-01")
    bind_request_actor(req)
    assert peek_actor_display_name() == "Maria Silva"
    assert peek_actor_client_id() == "mfe-01"


def test_bind_without_user_keeps_actor_none() -> None:
    req = _request(user=None)
    bind_request_actor(req)
    assert peek_actor_display_name() is None
    assert peek_actor_client_id() is None


def test_uuid_display_name_is_filtered() -> None:
    req = _request(user={"name": "3bfdd634-a3a5-41af-b6b3-607025c2bdf5"})
    bind_request_actor(req)
    assert peek_actor_display_name() is None


def test_actor_values_do_not_leak_to_parent_context() -> None:
    # Cada requisição roda num contexto-filho (cópia do contexto do servidor);
    # valores setados no filho herdam para o handler mas nunca voltam ao pai,
    # que é de onde a próxima requisição parte — sem reset necessário.
    child = contextvars.copy_context()

    def serve() -> None:
        req = _request(user={"name": "Maria"})
        bind_request_actor(req)
        assert peek_actor_display_name() == "Maria"

    child.run(serve)
    assert peek_actor_display_name() is None
    assert peek_actor_client_id() is None


def test_concurrent_requests_keep_own_actor() -> None:
    async def serve(name: str) -> str | None:
        req = _request(user={"name": name})
        bind_request_actor(req)
        await asyncio.sleep(0)
        return peek_actor_display_name()

    async def gather():
        return await asyncio.gather(serve("Ana"), serve("Beto"))

    a, b = asyncio.new_event_loop().run_until_complete(gather())
    assert {a, b} == {"Ana", "Beto"}


def test_middleware_binds_only_scoped_prefix() -> None:
    async def call_next(_req):
        return peek_actor_display_name()

    scoped = asyncio.new_event_loop().run_until_complete(
        actor_binding_middleware(_request("/seller-portfolios", user={"name": "Ana"}), call_next)
    )
    unscoped = asyncio.new_event_loop().run_until_complete(
        actor_binding_middleware(_request("/open-orders", user={"name": "Ana"}), call_next)
    )
    nested = asyncio.new_event_loop().run_until_complete(
        actor_binding_middleware(
            _request("/seller-portfolios/me", user={"name": "Ana"}), call_next
        )
    )
    lookalike = asyncio.new_event_loop().run_until_complete(
        actor_binding_middleware(
            _request("/seller-portfoliosx", user={"name": "Ana"}), call_next
        )
    )
    assert scoped == "Ana"
    assert nested == "Ana"
    assert unscoped is None
    assert lookalike is None


def test_middleware_strips_root_path_prefix() -> None:
    async def call_next(_req):
        return peek_actor_display_name()

    req = _request(
        "/apps/commercial-api/seller-portfolios",
        root_path="/apps/commercial-api",
        user={"name": "Beto"},
    )
    bound = asyncio.new_event_loop().run_until_complete(
        actor_binding_middleware(req, call_next)
    )
    assert bound == "Beto"
