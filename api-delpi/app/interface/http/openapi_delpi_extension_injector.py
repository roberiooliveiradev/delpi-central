"""Injeta extensão x-delpi no OpenAPI a partir de route_contract_registry — Playbook 22."""

from __future__ import annotations

from typing import Any

from app.interface.http.route_contract_registry import (
    ROUTE_CONTRACTS,
    presentation_strategy_for_entity,
    resolve_contract,
)

HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete", "head", "options"})


def build_x_delpi_extension(operation_id: str) -> dict[str, Any]:
    contract = ROUTE_CONTRACTS.get(str(operation_id or "").strip())

    if contract is not None:
        entity, shape = contract.entity, contract.shape
    else:
        entity, shape = resolve_contract(operation_id)

    strategy = presentation_strategy_for_entity(entity)

    return {
        "entity": entity,
        "shape": shape,
        "presentation": {"strategy": strategy},
    }


def inject_delpi_extensions(openapi_schema: dict[str, Any]) -> dict[str, int]:
    paths = openapi_schema.get("paths")

    if not isinstance(paths, dict):
        return {"operations": 0, "withDelpiExtension": 0, "skippedWithoutOperationId": 0}

    operations = 0
    with_extension = 0
    skipped = 0

    for path_item in paths.values():
        if not isinstance(path_item, dict):
            continue

        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue

            operations += 1
            operation_id = str(operation.get("operationId") or "").strip()

            if not operation_id:
                skipped += 1
                continue

            operation["x-delpi"] = build_x_delpi_extension(operation_id)
            with_extension += 1

    return {
        "operations": operations,
        "withDelpiExtension": with_extension,
        "skippedWithoutOperationId": skipped,
    }
