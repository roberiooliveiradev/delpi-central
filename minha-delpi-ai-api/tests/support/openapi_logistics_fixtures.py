"""Load logistics OpenAPI fixture and normalize imported actions for tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.infrastructure.external_actions.openapi_action_importer import (
    OpenApiActionImporter,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "fixtures" / "openapi" / "logistics_example.json"
)

PROVIDER_KEY = "logistics-example"


def load_logistics_openapi() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def import_logistics_actions(
    *,
    provider_key: str = PROVIDER_KEY,
    resolve_refs: bool | None = None,
) -> list[dict[str, Any]]:
    schema = load_logistics_openapi()
    should_resolve = resolve_refs
    if should_resolve is None:
        try:
            from app.infrastructure.openapi.openapi_ref_resolver import (  # noqa: F401
                OpenApiRefResolver,
            )

            should_resolve = True
        except ImportError:
            should_resolve = False
    if should_resolve:
        from app.infrastructure.openapi.openapi_ref_resolver import (
            OpenApiRefResolver,
        )

        schema = OpenApiRefResolver.resolve_document(schema)
    raw = OpenApiActionImporter().import_actions(provider_key, schema)
    return [normalize_imported_action(item, provider_key=provider_key) for item in raw]


def normalize_imported_action(
    action: dict[str, Any],
    *,
    provider_key: str = PROVIDER_KEY,
) -> dict[str, Any]:
    """Map importer snake_case payload to catalog camelCase used by selection."""
    return {
        "actionId": action.get("action_id") or action.get("actionId"),
        "operationId": action.get("operation_id") or action.get("operationId"),
        "method": action.get("method"),
        "path": action.get("path"),
        "summary": action.get("summary"),
        "description": action.get("description"),
        "tags": action.get("tags") or [],
        "parametersSchema": action.get("parameters_schema")
        or action.get("parametersSchema")
        or [],
        "requestBodySchema": action.get("request_body_schema")
        or action.get("requestBodySchema"),
        "responseSchema": action.get("response_schema") or action.get("responseSchema"),
        "sensitivity": action.get("sensitivity") or "read",
        "enabled": bool(action.get("enabled", True)),
        "deprecated": bool(action.get("deprecated", False)),
        "whenToUse": action.get("when_to_use") or action.get("whenToUse"),
        "whenNotToUse": action.get("when_not_to_use") or action.get("whenNotToUse"),
        "delpiMetadata": action.get("delpi_metadata") or action.get("delpiMetadata"),
        "providerKey": provider_key,
        "providerName": "Logistics Example API",
    }


def logistics_allowed_action_ids(actions: list[dict[str, Any]] | None = None) -> list[str]:
    rows = actions if actions is not None else import_logistics_actions()
    return [str(item["actionId"]) for item in rows if item.get("actionId")]


def find_logistics_action(
    operation_id: str,
    actions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rows = actions if actions is not None else import_logistics_actions()
    for item in rows:
        if str(item.get("operationId") or "") == operation_id:
            return item
    raise KeyError(f"operationId not found: {operation_id}")
