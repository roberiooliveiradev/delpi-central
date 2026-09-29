"""Unit tests for delpi_mcp.identity — S4 identity/request-context bridge."""

from __future__ import annotations

import asyncio

import pytest

from delpi_auth.request_context import (
    clear_current_user,
    clear_request_authorization,
    get_current_user,
    set_current_user,
    set_request_authorization,
)
from delpi_mcp.identity import (
    current_mcp_context,
    build_mcp_request,
    require_mcp_context,
)


class _User:
    def __init__(self, user_id: str) -> None:
        self.id = user_id
        self.email = f"{user_id}@example.test"


@pytest.fixture(autouse=True)
def _clean_context():
    clear_current_user()
    clear_request_authorization()
    yield
    clear_current_user()
    clear_request_authorization()


def test_current_context_reads_established_identity() -> None:
    user = _User("u-1")
    set_current_user(user)
    set_request_authorization("Bearer abc.def")
    ctx = current_mcp_context()
    assert ctx.user is user
    assert ctx.authorization == "Bearer abc.def"


def test_authorization_is_stripped() -> None:
    set_request_authorization("  Bearer padded  ")
    assert current_mcp_context().authorization == "Bearer padded"


def test_missing_context_returns_none_user() -> None:
    ctx = current_mcp_context()
    assert ctx.user is None
    assert ctx.authorization == ""


def test_require_context_fails_closed_without_user() -> None:
    with pytest.raises(PermissionError, match="Unauthorized"):
        require_mcp_context()


def test_require_context_returns_snapshot() -> None:
    user = _User("u-2")
    set_current_user(user)
    set_request_authorization("Bearer t")
    ctx = require_mcp_context()
    assert ctx.user is user


def test_build_request_preserves_user_object_and_authorization() -> None:
    user = _User("u-3")
    set_current_user(user)
    set_request_authorization("Bearer tok")
    ctx = require_mcp_context()
    request = build_mcp_request(
        context=ctx,
        server=("app", 443),
        client=("mcp-bridge", 0),
    )
    assert request.state.user is user
    assert request.headers["authorization"] == "Bearer tok"
    assert request.scope["path"] == "/mcp"
    assert request.scope["server"] == ("app", 443)


def test_build_request_extra_headers() -> None:
    user = _User("u-4")
    set_current_user(user)
    request = build_mcp_request(
        context=require_mcp_context(),
        server=("tv-dashboard-api", 443),
        client=("mcp-bridge", 0),
        extra_headers={"mcp-context": "tv-dashboard"},
    )
    assert request.headers["mcp-context"] == "tv-dashboard"
    assert "authorization" not in request.headers


def test_helpers_do_not_mutate_context() -> None:
    user = _User("u-5")
    set_current_user(user)
    set_request_authorization("Bearer keep")
    current_mcp_context()
    require_mcp_context()
    build_mcp_request(
        context=current_mcp_context(), server=("s", 1), client=("c", 0)
    )
    assert get_current_user() is user


def test_no_actor_crosstalk_between_tasks() -> None:
    async def run_actor(user_id: str, seen: list[str]) -> None:
        set_current_user(_User(user_id))
        await asyncio.sleep(0)  # interleave
        ctx = require_mcp_context()
        seen.append(ctx.user.id)

    async def main() -> list[str]:
        seen: list[str] = []
        await asyncio.gather(run_actor("actor-A", seen), run_actor("actor-B", seen))
        return seen

    assert sorted(asyncio.run(main())) == ["actor-A", "actor-B"]


def test_concurrent_request_builds_keep_own_user() -> None:
    async def run_actor(user_id: str) -> str:
        set_current_user(_User(user_id))
        await asyncio.sleep(0)
        request = build_mcp_request(
            context=require_mcp_context(), server=("s", 1), client=("c", 0)
        )
        return request.state.user.id

    async def main() -> list[str]:
        return list(await asyncio.gather(run_actor("A"), run_actor("B")))

    assert sorted(asyncio.run(main())) == ["A", "B"]
