"""S2 unit tests for shared MCP ASGI/transport glue."""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any

import pytest

from delpi_mcp.transport import (
    combine_lifespans,
    mcp_mount_path_middleware,
    mcp_transport_security_settings,
    normalize_mcp_mount_path,
)

EXACT_PATHS = frozenset({"/mcp", "/apps/example-api/mcp"})


class _Request:
    def __init__(self, scope: dict[str, Any]) -> None:
        self.scope = scope


def _scope(path: str, **extra: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "type": "http",
        "method": "POST",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"foo=bar",
        "headers": [(b"authorization", b"Bearer x")],
        "root_path": "/apps/example-api",
        "client": ("10.0.0.1", 1234),
        "server": ("svc", 8000),
        "scheme": "https",
    }
    base.update(extra)
    return base


class TestNormalizePath:
    def test_exact_mcp_rewritten(self):
        assert normalize_mcp_mount_path("/mcp", EXACT_PATHS) == "/mcp/"

    def test_exact_public_path_rewritten(self):
        assert (
            normalize_mcp_mount_path("/apps/example-api/mcp", EXACT_PATHS)
            == "/apps/example-api/mcp/"
        )

    def test_trailing_slash_unchanged(self):
        assert normalize_mcp_mount_path("/mcp/", EXACT_PATHS) == "/mcp/"

    def test_subpath_unchanged(self):
        assert normalize_mcp_mount_path("/mcp/extra", EXACT_PATHS) == "/mcp/extra"

    def test_unrelated_unchanged(self):
        assert normalize_mcp_mount_path("/health", EXACT_PATHS) == "/health"


class TestMountMiddleware:
    def _run(self, scope: dict[str, Any]) -> dict[str, Any]:
        seen: dict[str, Any] = {}

        async def call_next(request):
            seen["scope"] = dict(request.scope)
            return "response"

        result = asyncio.run(mcp_mount_path_middleware(EXACT_PATHS)(_Request(scope), call_next))
        assert result == "response"
        return seen["scope"]

    def test_mcp_rewritten(self):
        scope = self._run(_scope("/mcp"))
        assert scope["path"] == "/mcp/"
        assert scope["raw_path"] == b"/mcp/"

    def test_mcp_slash_unchanged(self):
        scope = self._run(_scope("/mcp/"))
        assert scope["path"] == "/mcp/"
        assert scope["raw_path"] == b"/mcp/"

    def test_unrelated_path_unchanged(self):
        scope = self._run(_scope("/health"))
        assert scope["path"] == "/health"
        assert scope["raw_path"] == b"/health"

    def test_query_headers_method_root_path_preserved(self):
        scope = self._run(_scope("/mcp"))
        assert scope["query_string"] == b"foo=bar"
        assert scope["headers"] == [(b"authorization", b"Bearer x")]
        assert scope["method"] == "POST"
        assert scope["root_path"] == "/apps/example-api"
        assert scope["client"] == ("10.0.0.1", 1234)
        assert scope["scheme"] == "https"

    def test_missing_raw_path_key_safe(self):
        s = _scope("/mcp")
        del s["raw_path"]
        scope = self._run(s)
        assert scope["path"] == "/mcp/"
        assert "raw_path" not in scope

    def test_produces_no_response(self):
        async def call_next(request):
            return "inner"

        assert asyncio.run(
            mcp_mount_path_middleware(EXACT_PATHS)(_Request(_scope("/mcp")), call_next)
        ) == "inner"


class TestCombineLifespans:
    def _lifespan(self, name: str, events: list[str], fail: bool = False):
        @contextlib.asynccontextmanager
        async def _lf(app):
            events.append(f"start:{name}")
            if fail:
                raise RuntimeError(f"{name}-startup-failed")
            try:
                yield
            finally:
                events.append(f"stop:{name}")

        return _lf

    def test_both_lifespans_run_in_order(self):
        events: list[str] = []
        combined = combine_lifespans(
            self._lifespan("app", events), self._lifespan("mcp", events)
        )

        async def main():
            async with combined(object()):
                events.append("body")

        asyncio.run(main())
        assert events == ["start:app", "start:mcp", "body", "stop:mcp", "stop:app"]

    def test_shutdown_order_is_reverse(self):
        events: list[str] = []
        combined = combine_lifespans(
            self._lifespan("a", events),
            self._lifespan("b", events),
            self._lifespan("c", events),
        )

        async def main():
            async with combined(object()):
                pass

        asyncio.run(main())
        assert events == [
            "start:a",
            "start:b",
            "start:c",
            "stop:c",
            "stop:b",
            "stop:a",
        ]

    def test_startup_exception_propagates_and_unwinds(self):
        events: list[str] = []
        combined = combine_lifespans(
            self._lifespan("app", events), self._lifespan("mcp", events, fail=True)
        )

        async def main():
            async with combined(object()):
                pass

        with pytest.raises(RuntimeError, match="mcp-startup-failed"):
            asyncio.run(main())
        assert events == ["start:app", "start:mcp", "stop:app"]

    def test_shutdown_exception_propagates(self):
        @contextlib.asynccontextmanager
        async def bad_stop(app):
            yield
            raise RuntimeError("shutdown-failed")

        combined = combine_lifespans(self._lifespan("app", []), bad_stop)

        async def main():
            async with combined(object()):
                pass

        with pytest.raises(RuntimeError, match="shutdown-failed"):
            asyncio.run(main())

    def test_yield_state_preserved(self):
        combined = combine_lifespans(
            self._lifespan("app", []), yield_state={"seed": True}
        )

        async def main():
            async with combined(object()) as state:
                return state

        assert asyncio.run(main()) == {"seed": True}

    def test_default_yield_is_none(self):
        combined = combine_lifespans(self._lifespan("app", []))

        async def main():
            async with combined(object()) as state:
                return state

        assert asyncio.run(main()) is None


class TestTransportSecuritySettings:
    def test_settings_shape(self):
        pytest.importorskip("mcp.server.transport_security")
        settings = mcp_transport_security_settings(
            allowed_hosts=["localhost:*"], allowed_origins=["https://chatgpt.com"]
        )
        assert settings.enable_dns_rebinding_protection is True
        assert list(settings.allowed_hosts) == ["localhost:*"]
        assert list(settings.allowed_origins) == ["https://chatgpt.com"]
