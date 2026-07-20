"""x-delpi no OpenAPI — Playbook 22 Fase D + locale.en nativo (Swagger)."""

from app.interface.http.openapi_delpi_extension_injector import (
    apply_native_openapi_from_locale,
    build_x_delpi_extension,
    inject_delpi_extensions,
)
from app.main import app


def test_build_x_delpi_extension_from_route_contract():
    extension = build_x_delpi_extension("get_product_stock", param_names=set())

    assert extension["entity"] == "product_stock"
    assert extension["shape"] == "paged_list"
    assert extension["presentation"]["strategy"] == "enriched"


def test_build_x_delpi_extension_scalar_stays_as_delivered():
    extension = build_x_delpi_extension("get_supplies_cpv", param_names=set())

    assert extension["entity"] == "supplies_cpv"
    assert extension["shape"] == "scalar"
    assert extension["presentation"]["strategy"] == "as_delivered"


def test_build_x_delpi_extension_includes_tv_audience_when_curated():
    extension = build_x_delpi_extension("get_overall_equipment_effectiveness_pct")

    assert extension["entity"]
    assert extension["shape"]
    tv = extension.get("tv") or {}
    assert "whenToUse" in tv
    assert "OEE" in tv["whenToUse"] or "oee" in tv["whenToUse"].lower() or "KPI" in tv["whenToUse"]
    locale = extension.get("locale") or {}
    assert "en" in locale and "pt-BR" in locale
    assert extension.get("category") == "production"


def test_build_x_delpi_extension_department_idd_locale():
    extension = build_x_delpi_extension(
        "get_dashboard_department_idd",
        param_names={"department_id"},
    )
    assert extension["entity"] == "dashboard_department_idd"
    assert extension["locale"]["pt-BR"]["summary"]
    assert extension["params"]["department_id"]["locale"]["pt-BR"]["label"] == "Departamento"
    assert "branch" not in extension.get("params", {})


def test_inject_delpi_extensions_applies_native_en_from_locale():
    schema = {
        "paths": {
            "/financial/rol": {
                "get": {
                    "operationId": "get_financial_rol",
                    "summary": "ROL financeiro (receita operacional líquida)",
                    "description": "Texto PT do agent_route",
                    "parameters": [
                        {"name": "branch", "in": "query", "description": "branch"},
                        {"name": "start_date", "in": "query", "description": "start_date"},
                    ],
                }
            }
        }
    }

    stats = inject_delpi_extensions(schema)
    assert stats["withDelpiExtension"] == 1
    op = schema["paths"]["/financial/rol"]["get"]
    assert op["x-delpi"]["locale"]["en"]["summary"]
    assert op["summary"] == op["x-delpi"]["locale"]["en"]["summary"]
    assert "financeiro" not in op["summary"].lower() or "financial" in op["summary"].lower()
    assert op["parameters"][0]["description"] != "branch"
    assert "branch" in op["parameters"][0]["description"].lower() or "Protheus" in op["parameters"][0]["description"]


def test_apply_native_openapi_from_locale_keeps_rich_param_description():
    operation = {
        "summary": "Old",
        "parameters": [
            {"name": "branch", "description": "Already documented in English for Protheus branch."},
        ],
    }
    extension = {
        "locale": {"en": {"summary": "Financial ROL", "description": "Financial ROL KPI."}},
        "params": {
            "branch": {"locale": {"en": {"label": "Branch", "description": "Branch code."}}},
        },
    }
    apply_native_openapi_from_locale(operation, extension)
    assert operation["summary"] == "Financial ROL"
    assert operation["parameters"][0]["description"].startswith("Already documented")


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

    assert not missing_extension, (
        "operationIds publicados sem x-delpi: "
        f"{sorted(missing_extension)[:20]}"
    )
    assert not mismatches, f"x-delpi divergente do registry: {sorted(mismatches)[:20]}"
