"""Injeta extensão x-delpi no OpenAPI a partir de route_contract_registry — Playbook 22."""

from __future__ import annotations

from typing import Any

from app.interface.http.route_contract_registry import (
    ROUTE_CONTRACTS,
    presentation_strategy_for_entity,
    resolve_contract,
)
from app.domain.services.route_locale_catalog_service import apply_route_locale_to_x_delpi

HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete", "head", "options"})


def build_x_delpi_extension(
    operation_id: str,
    *,
    param_names: set[str] | frozenset[str] | None = None,
) -> dict[str, Any]:
    contract = ROUTE_CONTRACTS.get(str(operation_id or "").strip())

    if contract is not None:
        entity, shape = contract.entity, contract.shape
    else:
        entity, shape = resolve_contract(operation_id)

    strategy = presentation_strategy_for_entity(entity)

    extension: dict[str, Any] = {
        "entity": entity,
        "shape": shape,
        "presentation": {"strategy": strategy},
    }
    return apply_route_locale_to_x_delpi(extension, operation_id, param_names=param_names)


def _parameter_names_from_operation(operation: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for param in operation.get("parameters") or []:
        if not isinstance(param, dict):
            continue
        name = str(param.get("name") or "").strip()
        if name:
            names.add(name)
    return names


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

            operation["x-delpi"] = build_x_delpi_extension(
                operation_id,
                param_names=_parameter_names_from_operation(operation),
            )
            with_extension += 1

    return {
        "operations": operations,
        "withDelpiExtension": with_extension,
        "skippedWithoutOperationId": skipped,
    }
