"""Composition wiring for DAVI dynamic READ (ports + approved capability runners)."""

from __future__ import annotations

from typing import Any


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


class _RequestBoundCatalogActionExecutor:
    """Bind per-request Authorization into infrastructure (Composition only)."""

    def __init__(self, authorization: str | None) -> None:
        self._authorization = authorization

    def execute(
        self,
        *,
        action_id: str,
        validated_arguments: dict[str, Any],
    ):
        from app.domain.ports.davi_catalog_action_executor_port import (
            CatalogActionExecutionResult,
        )
        from app.infrastructure.davi.asgi_catalog_action_executor import (
            AsgiCatalogActionExecutor,
        )
        from app.infrastructure.davi.in_process_asgi_client import (
            open_in_process_asgi_client,
        )
        from app.main import app

        if not self._authorization:
            return CatalogActionExecutionResult(outcome="unauthorized")
        with open_in_process_asgi_client(app) as client:
            return AsgiCatalogActionExecutor(
                client, authorization=self._authorization
            ).execute(
                action_id=action_id,
                validated_arguments=validated_arguments,
            )


def davi_read_wired(
    *,
    authorization: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Read tool wiring: request-bound executor + approved capability runner."""
    from app.application.external_capabilities.dynamic_information.execute_service import (
        davi_read,
    )

    return davi_read(
        catalog_action_executor=_RequestBoundCatalogActionExecutor(authorization),
        search_products_runner=_search_products_runner,
        **kwargs,
    )


def davi_analyze_wired(
    *,
    authorization: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Analyze tool wiring: request-bound executor + approved capability runner."""
    from app.application.external_capabilities.dynamic_information.execute_service import (
        davi_analyze,
    )

    return davi_analyze(
        catalog_action_executor=_RequestBoundCatalogActionExecutor(authorization),
        search_products_runner=_search_products_runner,
        **kwargs,
    )


def davi_knowledge_wired(
    *,
    authorization: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Knowledge tool wiring: request-bound executor + published corpus index."""
    from app.application.external_capabilities.dynamic_information.knowledge_service import (
        davi_knowledge,
    )
    from app.composition.governed_knowledge_composer import (
        published_knowledge_topics,
    )

    return davi_knowledge(
        catalog_action_executor=_RequestBoundCatalogActionExecutor(authorization),
        sources_provider=published_knowledge_topics,
        **kwargs,
    )
