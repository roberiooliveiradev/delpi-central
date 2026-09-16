"""In-process ASGI GET client for DAVI catalog actions (no lifespan re-entry)."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import httpx
from anyio.from_thread import start_blocking_portal


class InProcessAsgiClient:
    """Sync HTTP-shaped client over the live ASGI app.

    Uses ``httpx.ASGITransport`` so the hosting process lifespan (including MCP
    ``StreamableHTTPSessionManager``) is **not** re-entered. ``TestClient(app)``
    as a context manager re-runs lifespan and raises::

        RuntimeError: StreamableHTTPSessionManager .run() can only be called once

    when catalog actions execute inside an already-running api-delpi process.
    """

    def __init__(self, app: Any):
        self._app = app

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        async def _request() -> httpx.Response:
            transport = httpx.ASGITransport(app=self._app)
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://davi-internal",
            ) as client:
                return await client.get(path, params=params, headers=headers)

        with start_blocking_portal() as portal:
            return portal.call(_request)


@contextmanager
def open_in_process_asgi_client(app: Any) -> Iterator[InProcessAsgiClient]:
    """Yield a lifespan-safe in-process ASGI client for the given app."""
    yield InProcessAsgiClient(app)
