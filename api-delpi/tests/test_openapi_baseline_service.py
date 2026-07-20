from app.domain.services.openapi_baseline_service import (
    BASELINE_VERSION,
    build_baseline_payload,
    extract_operations_from_openapi,
    extract_x_delpi,
    simplify_openapi_parameter,
)


def test_simplify_openapi_parameter_query_only() -> None:
    assert simplify_openapi_parameter({"in": "path", "name": "id"}) is None
    entry = simplify_openapi_parameter(
        {
            "in": "query",
            "name": "branch",
            "required": False,
            "description": "Filial",
            "schema": {"type": "string", "default": "01"},
        }
    )
    assert entry == {
        "name": "branch",
        "required": False,
        "description": "Filial",
        "type": "string",
        "default": "01",
    }


def test_simplify_openapi_parameter_anyof_null() -> None:
    entry = simplify_openapi_parameter(
        {
            "in": "query",
            "name": "branch",
            "required": False,
            "schema": {
                "anyOf": [
                    {"type": "string", "minLength": 2, "maxLength": 2},
                    {"type": "null"},
                ],
                "title": "Branch",
            },
        }
    )
    assert entry is not None
    assert entry["type"] == "string"
    assert entry["name"] == "branch"


def test_extract_operations_includes_parameters_and_x_delpi() -> None:
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "1"},
        "paths": {
            "/commercial/closing-rate": {
                "get": {
                    "operationId": "get_sales_conversion_rate",
                    "summary": "Taxa",
                    "tags": ["Comercial"],
                    "parameters": [
                        {
                            "in": "query",
                            "name": "start_date",
                            "schema": {"type": "string"},
                        },
                        {
                            "in": "query",
                            "name": "end_date",
                            "schema": {"type": "string"},
                        },
                        {
                            "in": "query",
                            "name": "customer_segment",
                            "schema": {"type": "string", "enum": ["weg", "new_business"]},
                        },
                    ],
                    "x-delpi": {
                        "entity": "sales_conversion_rate",
                        "shape": "scalar",
                        "presentation": {"strategy": "kpi"},
                    },
                }
            }
        },
    }
    ops = extract_operations_from_openapi(spec)
    assert len(ops) == 1
    op = ops[0]
    assert op["operationId"] == "get_sales_conversion_rate"
    names = {p["name"] for p in op["parameters"]}
    assert names == {"start_date", "end_date", "customer_segment"}
    assert op["xDelpi"]["shape"] == "scalar"
    assert op["xDelpi"]["entity"] == "sales_conversion_rate"

    payload = build_baseline_payload(spec)
    assert payload["version"] == BASELINE_VERSION
    assert payload["operation_count"] == 1


def test_extract_x_delpi_persists_locale_params_category() -> None:
    extension = extract_x_delpi(
        {
            "x-delpi": {
                "entity": "dashboard_department_idd",
                "shape": "scalar",
                "presentation": {"strategy": "as_delivered"},
                "category": "system",
                "locale": {
                    "en": {"summary": "Department IDD score"},
                    "pt-BR": {"summary": "IDD departamental", "whenToUse": "Card KPI"},
                },
                "params": {
                    "department_id": {
                        "locale": {
                            "en": {"label": "Department"},
                            "pt-BR": {"label": "Departamento"},
                        }
                    }
                },
                "tv": {"whenToUse": "Card KPI", "label": "IDD departamental"},
            }
        }
    )
    assert extension is not None
    assert extension["category"] == "system"
    assert extension["locale"]["en"]["summary"] == "Department IDD score"
    assert extension["params"]["department_id"]["locale"]["pt-BR"]["label"] == "Departamento"
    assert extension["tv"]["whenToUse"] == "Card KPI"
    assert BASELINE_VERSION == "3"


def test_extract_operations_merges_audience_locale() -> None:
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "1"},
        "paths": {
            "/dashboard/department-idd": {
                "get": {
                    "operationId": "get_dashboard_department_idd",
                    "summary": "Department IDD score",
                    "tags": ["Dashboard"],
                    "parameters": [
                        {
                            "in": "query",
                            "name": "department_id",
                            "required": True,
                            "schema": {
                                "type": "string",
                                "enum": ["commercial", "hr"],
                            },
                        }
                    ],
                    "x-delpi": {
                        "entity": "dashboard_department_idd",
                        "shape": "scalar",
                        "presentation": {"strategy": "as_delivered"},
                    },
                }
            }
        },
    }
    ops = extract_operations_from_openapi(spec)
    assert len(ops) == 1
    x_delpi = ops[0]["xDelpi"]
    assert x_delpi["entity"] == "dashboard_department_idd"
    assert x_delpi.get("locale", {}).get("pt-BR", {}).get("whenToUse")
    assert ops[0]["parameters"][0]["enum"] == ["commercial", "hr"]
