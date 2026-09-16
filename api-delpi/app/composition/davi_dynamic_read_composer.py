"""Composition wiring for DAVI dynamic READ (ports + approved capability runners)."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator


@contextmanager
def open_api_delpi_asgi_client() -> Iterator[Any]:
    """Yield a TestClient bound to the api-delpi FastAPI app (Composition Root only)."""
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


def _search_products_runner(**kwargs: Any) -> dict[str, Any]:
    from app.application.external_capabilities.product_search_service import (
        search_products,
    )
    from app.composition.product_composer import build_search_products_use_case

    return search_products(
        search_use_case=build_search_products_use_case(),
        **kwargs,
    )


def execute_delpi_information_wired(**kwargs: Any) -> dict[str, Any]:
    """Wire approved Product Master path + lazy catalog-fixed GET adapter."""
    from app.application.external_capabilities.dynamic_information.execute_service import (
        execute_delpi_information,
    )
    from app.infrastructure.davi.asgi_catalog_fixed_get_adapter import (
        AsgiCatalogFixedGetAdapter,
    )

    class _LazyCatalogGetPort:
        def execute(self, request, *, authorization: str):
            with open_api_delpi_asgi_client() as client:
                return AsgiCatalogFixedGetAdapter(client).execute(
                    request, authorization=authorization
                )

    return execute_delpi_information(
        catalog_get_port=_LazyCatalogGetPort(),
        search_products_runner=_search_products_runner,
        **kwargs,
    )
