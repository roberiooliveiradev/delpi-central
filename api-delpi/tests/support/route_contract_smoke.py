"""Helpers canônicos para smoke de contrato HTTP (envelope meta)."""

from __future__ import annotations

import json
from typing import Any

from app.application.services.response_meta_builder import DATA_VERSION
from app.interface.http.route_contract_registry import ROUTE_CONTRACTS, resolve_contract


def body_json(response: Any) -> dict[str, Any]:
    raw = getattr(response, "body", None)
    if raw is not None:
        return json.loads(raw.decode())
    # Starlette/FastAPI TestClient Response
    return response.json()


def assert_envelope_meta(
    body: dict[str, Any],
    *,
    operation_id: str,
    shape: str | None = None,
    entity: str | None = None,
) -> None:
    assert body.get("success") is True, body
    meta = body.get("meta")
    assert isinstance(meta, dict), body
    assert meta.get("operationId") == operation_id, meta
    expected_entity, expected_shape = resolve_contract(
        operation_id, entity=entity, shape=shape
    )
    if shape is not None:
        expected_shape = shape
    if entity is not None:
        expected_entity = entity
    assert meta.get("shape") == expected_shape, meta
    assert meta.get("entity") == expected_entity, meta
    assert meta.get("dataVersion") == DATA_VERSION, meta
    contract = ROUTE_CONTRACTS.get(operation_id)
    if contract is not None and shape is None and entity is None:
        assert contract.entity == expected_entity
        assert contract.shape == expected_shape


def effective_route_paths(routes: Any) -> set[str]:
    """Resolve route paths including lazily included routers (FastAPI _IncludedRouter)."""
    paths: set[str] = set()
    for route in routes:
        path = getattr(route, "path", None)
        if path:
            paths.add(path)
            continue
        context = getattr(route, "include_context", None)
        original = getattr(route, "original_router", None)
        if context is None or original is None:
            continue
        prefix = getattr(context, "prefix", "") or ""
        for child in getattr(original, "routes", []):
            child_path = getattr(child, "path", None)
            if child_path:
                paths.add(f"{prefix}{child_path}")
    return paths
