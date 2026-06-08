"""Smoke Fase 4: OpenAPI descreve schemas e examples das rotas chat-critical."""

from app.main import app


CHAT_CRITICAL_OPERATIONS = {
    "search_products",
    "get_product_stock",
    "get_product_structure",
    "get_product_analyser",
    "get_product_factory_status",
    "get_product_summary",
    "get_product_detail",
}


def _operation_map(openapi_schema: dict) -> dict[str, dict]:
    mapping: dict[str, dict] = {}

    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId")
            if operation_id:
                mapping[operation_id] = operation

    return mapping


def _resolve_schema(openapi_schema: dict, schema: dict) -> dict:
    ref = schema.get("$ref")

    if not isinstance(ref, str) or not ref.startswith("#/components/schemas/"):
        return schema

    name = ref.rsplit("/", 1)[-1]
    components = openapi_schema.get("components") or {}
    resolved = (components.get("schemas") or {}).get(name) or {}

    return resolved if isinstance(resolved, dict) else schema


def test_chat_critical_operations_document_response_schema() -> None:
    openapi_schema = app.openapi()
    operations = _operation_map(openapi_schema)
    missing = CHAT_CRITICAL_OPERATIONS - set(operations)
    assert not missing, f"operationIds ausentes: {sorted(missing)}"

    documented = 0
    for operation_id in CHAT_CRITICAL_OPERATIONS:
        operation = operations[operation_id]
        responses = operation.get("responses") or {}
        ok = responses.get("200") or responses.get(200)
        assert isinstance(ok, dict), operation_id

        content = ok.get("content") or {}
        json_content = content.get("application/json") or {}
        schema = _resolve_schema(openapi_schema, json_content.get("schema") or {})
        assert schema, f"schema vazio em {operation_id}"

        properties = schema.get("properties") or {}
        assert "data" in properties, f"schema sem data em {operation_id}"
        documented += 1

    assert documented >= 6


def test_stock_operation_has_openapi_example() -> None:
    openapi_schema = app.openapi()
    operations = _operation_map(openapi_schema)
    operation = operations["get_product_stock"]
    json_content = operation["responses"]["200"]["content"]["application/json"]
    assert "example" in json_content or "examples" in json_content
