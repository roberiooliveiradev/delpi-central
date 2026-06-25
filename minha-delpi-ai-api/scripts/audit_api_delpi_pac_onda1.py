#!/usr/bin/env python3
"""Gate Onda 1 PAC — rotas expostas pela api-delpi (não provider separado)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_PATH = (
    ROOT / "app" / "content" / "pt-BR" / "assistant" / "openapi_operation_contracts.json"
)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ONDA1_OPERATION_IDS = (
    "get_quality_action_plans_dashboard",
    "list_quality_action_plans_overdue",
    "list_quality_action_plans",
    "get_quality_action_plan_detail",
    "create_quality_action_plan",
    "update_quality_action_plan",
    "update_quality_action_plan_status",
    "upsert_quality_action_plan_ishikawa",
    "upsert_quality_action_plan_five_whys",
    "create_quality_action_plan_actions",
    "update_quality_action_plan_action",
    "record_quality_action_plan_effectiveness",
    "upsert_quality_action_plan_rnc_8d",
    "export_quality_action_plan_rnc_8d",
    "list_quality_action_plan_evidences",
    "attach_quality_action_plan_evidence",
    "delete_quality_action_plan_evidence",
    "get_quality_action_plan_similar_cases",
)

ONDA1_REQUIRED_OPENAPI_PATHS = (
    "/quality/action-plans",
    "/quality/action-plans/dashboard",
    "/quality/action-plans/overdue",
    "/quality/action-plans/{plan_id}",
    "/quality/action-plans/{plan_id}/similar-cases",
    "/quality/action-plans/{plan_id}/rnc-8d",
    "/quality/action-plans/{plan_id}/export/rnc-8d",
    "/quality/action-plans/{plan_id}/evidences",
    "/quality/action-plans/{plan_id}/ishikawa",
    "/quality/action-plans/{plan_id}/five-whys",
    "/quality/action-plans/{plan_id}/actions",
    "/quality/action-plans/{plan_id}/actions/{action_id}",
)


def _load_schema_from_url(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("OpenAPI inválido")

    return payload


def _load_schema_from_api_delpi() -> dict[str, Any]:
    url = os.environ.get(
        "API_DELPI_OPENAPI_URL",
        "http://api-delpi:8000/openapi.json",
    ).strip()

    if url:
        try:
            return _load_schema_from_url(url)
        except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError):
            pass

    api_delpi_root = Path(__file__).resolve().parents[2] / "api-delpi"

    if not api_delpi_root.is_dir():
        raise ValueError(
            "Não foi possível carregar OpenAPI da api-delpi "
            f"(URL={url!r} e checkout ausente em {api_delpi_root})",
        )

    api_delpi_path = str(api_delpi_root)
    removed = sys.path.pop(0) if sys.path and sys.path[0] == str(ROOT) else None

    if api_delpi_path not in sys.path:
        sys.path.insert(0, api_delpi_path)

    try:
        from app.main import app as api_delpi_app

        schema = api_delpi_app.openapi()
    finally:
        if sys.path and sys.path[0] == api_delpi_path:
            sys.path.pop(0)

        if removed is not None:
            sys.path.insert(0, removed)

    if not isinstance(schema, dict):
        raise ValueError("api-delpi OpenAPI inválido")

    return schema


def _operation_index(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    paths = schema.get("paths")

    if not isinstance(paths, dict):
        return {}

    index: dict[str, dict[str, Any]] = {}

    for path_item in paths.values():
        if not isinstance(path_item, dict):
            continue

        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue

            operation_id = str(operation.get("operationId") or "").strip()

            if operation_id:
                index[operation_id] = operation

    return index


def _load_contracts_index() -> dict[str, dict[str, str]]:
    if not CONTRACTS_PATH.is_file():
        return {}

    payload = json.loads(CONTRACTS_PATH.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        return {}

    return {
        str(operation_id): contract
        for operation_id, contract in payload.items()
        if isinstance(contract, dict)
    }


def validate(schema: dict[str, Any]) -> dict[str, Any]:
    from app.composition.content_composer import configure_domain_infrastructure_ports
    from app.domain.services.openapi_delpi_extension_service import (
        OpenApiDelpiExtensionService,
    )

    configure_domain_infrastructure_ports()

    paths = schema.get("paths") if isinstance(schema.get("paths"), dict) else {}
    missing_paths = [path for path in ONDA1_REQUIRED_OPENAPI_PATHS if path not in paths]
    operations = _operation_index(schema)
    missing_operation_ids = [
        operation_id
        for operation_id in ONDA1_OPERATION_IDS
        if operation_id not in operations
    ]
    missing_x_delpi: list[str] = []
    contract_mismatches: list[str] = []
    contracts = _load_contracts_index()

    for operation_id in ONDA1_OPERATION_IDS:
        operation = operations.get(operation_id)

        if not isinstance(operation, dict):
            continue

        extension = OpenApiDelpiExtensionService.extract_from_operation(operation)

        if not extension:
            missing_x_delpi.append(operation_id)
            continue

        contract = contracts.get(operation_id)

        if contract is None:
            continue

        if extension.get("entity") != contract.get("entity") or extension.get("shape") != contract.get(
            "shape"
        ):
            contract_mismatches.append(operation_id)

    ok = not (
        missing_paths
        or missing_operation_ids
        or missing_x_delpi
        or contract_mismatches
    )

    return {
        "ok": ok,
        "missingPaths": missing_paths,
        "missingOperationIds": missing_operation_ids,
        "missingXDelpi": missing_x_delpi,
        "contractMismatches": contract_mismatches,
        "operationCount": len(operations),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Exit 1 quando houver gaps.")
    parser.add_argument("--json", action="store_true", help="Imprime relatório JSON.")
    args = parser.parse_args()

    report = validate(_load_schema_from_api_delpi())

    if args.json or not args.check:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.check and not report["ok"]:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
