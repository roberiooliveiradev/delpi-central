"""Composition wiring for DAVI dynamic READ governed HTTP client."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator


@contextmanager
def open_api_delpi_asgi_client() -> Iterator[Any]:
    """Yield a TestClient bound to the api-delpi FastAPI app (Composition Root)."""
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        yield client


def refresh_davi_action_index_from_live_openapi() -> int:
    """Refresh technical action index from live OpenAPI when available."""
    from app.main import app
    from app.application.external_capabilities.dynamic_information.action_index import (
        seed_actions_from_openapi,
    )

    actions = seed_actions_from_openapi(app.openapi())
    return len(actions)


def execute_delpi_information_wired(**kwargs):
    from app.application.external_capabilities.dynamic_information.execute_service import (
        execute_delpi_information,
    )

    with open_api_delpi_asgi_client() as client:
        return execute_delpi_information(http_client=client, **kwargs)
