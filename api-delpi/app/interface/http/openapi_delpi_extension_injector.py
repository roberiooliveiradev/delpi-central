"""Injeta extensão x-delpi no OpenAPI e alinha summary/description nativos (EN) para Swagger."""

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


def apply_native_openapi_from_locale(operation: dict[str, Any], extension: dict[str, Any]) -> None:
    """Swagger lê summary/description/param.description nativos — preencher a partir de locale.en."""
    locale = extension.get("locale") if isinstance(extension.get("locale"), dict) else {}
    en = locale.get("en") if isinstance(locale.get("en"), dict) else {}
    summary = str(en.get("summary") or "").strip()
    description = str(en.get("description") or summary).strip()
    if summary:
        operation["summary"] = summary
    if description:
        operation["description"] = description

    params_locale = extension.get("params") if isinstance(extension.get("params"), dict) else {}
    for param in operation.get("parameters") or []:
        if not isinstance(param, dict):
            continue
        name = str(param.get("name") or "").strip()
        if not name:
            continue
        entry = params_locale.get(name) if isinstance(params_locale.get(name), dict) else {}
        p_locale = entry.get("locale") if isinstance(entry.get("locale"), dict) else {}
        p_en = p_locale.get("en") if isinstance(p_locale.get("en"), dict) else {}
        desc = str(p_en.get("description") or p_en.get("label") or "").strip()
        if not desc:
            continue
        current = str(param.get("description") or "").strip()
        # Substitui vazio, eco do nome do param, ou stub sem valor.
        if not current or current == name or current.lower() == name.lower():
            param["description"] = desc


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

            extension = build_x_delpi_extension(
                operation_id,
                param_names=_parameter_names_from_operation(operation),
            )
            operation["x-delpi"] = extension
            apply_native_openapi_from_locale(operation, extension)
            with_extension += 1

    return {
        "operations": operations,
        "withDelpiExtension": with_extension,
        "skippedWithoutOperationId": skipped,
    }
