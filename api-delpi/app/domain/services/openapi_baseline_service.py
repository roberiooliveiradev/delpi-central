"""Baseline OpenAPI versionado para diff de contrato (Fase 4 do console)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_BASELINE_PATH = Path(__file__).resolve().parents[2] / "content" / "openapi_baseline.json"

_HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete", "head", "options"})


def _operation_key(method: str, path: str) -> str:
    return f"{method.upper()} {path}"


def extract_operations_from_openapi(spec: dict[str, Any]) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []

    for path, methods in (spec.get("paths") or {}).items():
        if not isinstance(methods, dict):
            continue
        for method, operation in methods.items():
            if method not in _HTTP_METHODS or not isinstance(operation, dict):
                continue
            operations.append(
                {
                    "method": method.upper(),
                    "path": path,
                    "operationId": operation.get("operationId"),
                    "summary": operation.get("summary"),
                    "tags": operation.get("tags") or [],
                    "deprecated": bool(operation.get("deprecated")),
                }
            )

    operations.sort(key=lambda row: (row["path"], row["method"]))
    return operations


def build_baseline_payload(spec: dict[str, Any]) -> dict[str, Any]:
    info = spec.get("info") or {}
    return {
        "version": "1",
        "api_title": info.get("title"),
        "api_version": info.get("version"),
        "openapi_version": spec.get("openapi"),
        "operation_count": len(extract_operations_from_openapi(spec)),
        "operations": extract_operations_from_openapi(spec),
    }


def load_openapi_baseline() -> dict[str, Any]:
    raw = _BASELINE_PATH.read_text(encoding="utf-8")
    return json.loads(raw)


def save_openapi_baseline(spec: dict[str, Any]) -> Path:
    payload = build_baseline_payload(spec)
    _BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _BASELINE_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return _BASELINE_PATH
