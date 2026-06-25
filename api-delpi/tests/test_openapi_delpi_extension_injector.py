"""x-delpi no OpenAPI — Playbook 22 Fase D."""

from app.interface.http.openapi_delpi_extension_injector import (
    build_x_delpi_extension,
    inject_delpi_extensions,
)
from app.main import app


def test_build_x_delpi_extension_from_route_contract():
    extension = build_x_delpi_extension("get_product_stock")

    assert extension == {
        "entity": "product_stock",
        "shape": "paged_list",
        "presentation": {"strategy": "enriched"},
    }


def test_build_x_delpi_extension_scalar_stays_as_delivered():
    extension = build_x_delpi_extension("get_supplies_cpv")

    assert extension == {
        "entity": "supplies_cpv",
        "shape": "scalar",
        "presentation": {"strategy": "as_delivered"},
    }


def test_inject_delpi_extensions_on_operations_with_operation_id():
    schema = {
        "paths": {
            "/products/{code}/stock": {
                "get": {
                    "operationId": "get_product_stock",
                    "summary": "Estoque",
                }
            }
        }
    }

    stats = inject_delpi_extensions(schema)

    assert stats == {
        "operations": 1,
        "withDelpiExtension": 1,
        "skippedWithoutOperationId": 0,
    }
    assert schema["paths"]["/products/{code}/stock"]["get"]["x-delpi"]["entity"] == "product_stock"


def test_openapi_schema_exposes_x_delpi_for_chat_critical_routes():
    schema = app.openapi()
    missing: list[str] = []

    for path_item in schema.get("paths", {}).values():
        if not isinstance(path_item, dict):
            continue

        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue

            operation_id = str(operation.get("operationId") or "").strip()

            if not operation_id:
                continue

            extension = operation.get("x-delpi")

            if not isinstance(extension, dict) or not extension.get("entity") or not extension.get("shape"):
                missing.append(operation_id)

    assert not missing, f"operationIds sem x-delpi válido: {sorted(missing)[:20]}"


def test_all_published_openapi_operations_have_x_delpi_matching_registry():
    from app.interface.http.route_contract_registry import ROUTE_CONTRACTS

    schema = app.openapi()
    missing_extension: list[str] = []
    mismatches: list[str] = []

    for path_item in schema.get("paths", {}).values():
        if not isinstance(path_item, dict):
            continue

        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue

            operation_id = str(operation.get("operationId") or "").strip()

            if not operation_id:
                continue

            extension = operation.get("x-delpi")

            if (
                not isinstance(extension, dict)
                or not extension.get("entity")
                or not extension.get("shape")
            ):
                missing_extension.append(operation_id)
                continue

            contract = ROUTE_CONTRACTS.get(operation_id)

            if contract is None:
                continue

            if extension.get("entity") != contract.entity or extension.get("shape") != contract.shape:
                mismatches.append(operation_id)

            presentation = extension.get("presentation") or {}

            if presentation.get("strategy") != "as_delivered":
                mismatches.append(operation_id)

    assert not missing_extension, (
        "operationIds publicados sem x-delpi: "
        f"{sorted(missing_extension)[:20]}"
    )
    assert not mismatches, f"x-delpi divergente do registry: {sorted(mismatches)[:20]}"
