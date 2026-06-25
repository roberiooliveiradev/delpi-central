#!/usr/bin/env python3
"""Gate: operações OpenAPI publicadas com x-delpi / delpi_metadata extraível (Fase 13)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.openapi_delpi_extension_service import (
    OpenApiDelpiExtensionService,
)

configure_domain_infrastructure_ports()

HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete"})
SKIP_PATH_PREFIXES = ("/health",)


def _operation_entries(schema: dict[str, Any]) -> list[dict[str, str]]:
    paths = schema.get("paths")

    if not isinstance(paths, dict):
        return []

    entries: list[dict[str, str]] = []

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        path_token = str(path or "").strip()

        if any(path_token.startswith(prefix) for prefix in SKIP_PATH_PREFIXES):
            continue

        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue

            entries.append(
                {
                    "method": method.upper(),
                    "path": path_token,
                    "operationId": str(operation.get("operationId") or "").strip(),
                }
            )

    return entries


def validate_schema(schema: dict[str, Any]) -> dict[str, Any]:
    missing: list[dict[str, str]] = []

    for entry in _operation_entries(schema):
        operation = (
            schema.get("paths", {})
            .get(entry["path"], {})
            .get(entry["method"].lower(), {})
        )

        if not isinstance(operation, dict):
            continue

        if not OpenApiDelpiExtensionService.extract_from_operation(operation):
            missing.append(entry)

    coverage = OpenApiDelpiExtensionService.summarize_schema_coverage(schema)
    operations = len(_operation_entries(schema))

    return {
        "ok": not missing,
        "operations": operations,
        "withDelpiMetadata": operations - len(missing),
        "missingDelpiMetadata": missing,
        "schemaCoverage": coverage,
    }


def _load_api_delpi_schema() -> dict[str, Any]:
    import os
    import urllib.error
    import urllib.request

    url = os.environ.get(
        "API_DELPI_OPENAPI_URL",
        "http://api-delpi:8000/openapi.json",
    ).strip()

    if url:
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))

            if isinstance(payload, dict):
                return payload
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


def _load_schema_from_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("OpenAPI file must contain a JSON object")

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        choices=("api-delpi", "file"),
        default="api-delpi",
        help="Origem do schema (default: app OpenAPI do api-delpi).",
    )
    parser.add_argument(
        "--schema-file",
        type=Path,
        help="Arquivo OpenAPI JSON quando --source=file.",
    )
    parser.add_argument("--check", action="store_true", help="Exit 1 quando houver gaps.")
    parser.add_argument("--json", action="store_true", help="Imprime relatório JSON.")
    args = parser.parse_args()

    if args.source == "file":
        if not args.schema_file:
            print("error: --schema-file obrigatório com --source=file", file=sys.stderr)
            return 2

        schema = _load_schema_from_file(args.schema_file)
    else:
        schema = _load_api_delpi_schema()

    report = validate_schema(schema)

    if args.json or not args.check:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.check and not report["ok"]:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
