from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx
from delpi_auth.service_token import apply_internal_service_headers

from tv_app.application.services.data.tv_data_presentation_modes_service import suggested_display_modes
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService
from tv_app.config import settings

_HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete", "head", "options"})


def _slug_category(tags: list[Any] | None) -> str:
    if not tags:
        return "general"
    first = str(tags[0]).strip().lower()
    return first.replace(" ", "_").replace("-", "_") or "general"


def extract_get_operations_from_openapi(spec: dict[str, Any]) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    for path, methods in (spec.get("paths") or {}).items():
        if not isinstance(methods, dict):
            continue
        for method, operation in methods.items():
            if method not in _HTTP_METHODS or not isinstance(operation, dict):
                continue
            if method.upper() != "GET":
                continue
            operation_id = str(operation.get("operationId") or "").strip()
            if not operation_id:
                continue
            x_delpi = operation.get("x-delpi") if isinstance(operation.get("x-delpi"), dict) else {}
            operations.append(
                {
                    "operationId": operation_id,
                    "httpMethod": "GET",
                    "path": path,
                    "summary": operation.get("summary") or operation_id,
                    "tags": operation.get("tags") or [],
                    "category": _slug_category(operation.get("tags")),
                    "deprecated": bool(operation.get("deprecated")),
                    "metaShape": x_delpi.get("shape"),
                    "metaEntity": x_delpi.get("entity"),
                }
            )
    operations.sort(key=lambda row: (row["category"], row["path"]))
    return operations


def _baseline_path_candidates() -> list[Path]:
    raw = str(os.getenv("TV_DATA_OPENAPI_BASELINE_PATH") or "").strip()
    paths: list[Path] = []
    if raw:
        paths.append(Path(raw))
    paths.extend(
        [
            Path(__file__).resolve().parents[5] / "api-delpi" / "app" / "content" / "openapi_baseline.json",
            Path("/app/content/openapi_baseline.json"),
        ]
    )
    return paths


@lru_cache(maxsize=1)
def _load_baseline_operations() -> list[dict[str, Any]] | None:
    for path in _baseline_path_candidates():
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload.get("operations"), list):
            return [
                row
                for row in payload["operations"]
                if isinstance(row, dict) and str(row.get("method") or "").upper() == "GET"
            ]
        return extract_get_operations_from_openapi(payload)
    return None


class TvDataOpenApiCatalogService:
    """Inventário GET da api-delpi (OpenAPI live ou baseline) para curadoria do catálogo TV."""

    def __init__(self, allowlist: TvDataRouteCatalogService | None = None) -> None:
        self._allowlist = allowlist or TvDataRouteCatalogService()

    def fetch_live_openapi(self) -> dict[str, Any]:
        headers: dict[str, str] = {}
        apply_internal_service_headers(headers)
        caller = (settings.DELPI_API_CALLER_APP or "tv-dashboard-api").strip()
        if caller:
            headers["X-Delpi-Caller-App"] = caller
        base = (settings.DELPI_API_URL or "http://delpi-api-delpi:8000").rstrip("/")
        with httpx.Client(base_url=base, timeout=30.0) as client:
            response = client.get("/openapi.json", headers=headers)
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise ValueError("OpenAPI inválido.")
            return body

    def list_get_operations(self, *, prefer_live: bool = False) -> list[dict[str, Any]]:
        if prefer_live:
            try:
                return extract_get_operations_from_openapi(self.fetch_live_openapi())
            except Exception:
                pass
        baseline_rows = _load_baseline_operations()
        if baseline_rows is not None:
            return [
                {
                    "operationId": row.get("operationId"),
                    "httpMethod": "GET",
                    "path": row.get("path"),
                    "summary": row.get("summary"),
                    "tags": row.get("tags") or [],
                    "category": _slug_category(row.get("tags")),
                    "deprecated": bool(row.get("deprecated")),
                    "metaShape": None,
                    "metaEntity": None,
                }
                for row in baseline_rows
                if isinstance(row, dict) and row.get("operationId")
            ]
        return extract_get_operations_from_openapi(self.fetch_live_openapi())

    def list_candidates(self, *, include_allowlisted: bool = False) -> list[dict[str, Any]]:
        allowlisted = {str(row.get("operationId") or "") for row in self._allowlist.list_routes()}
        items: list[dict[str, Any]] = []
        for row in self.list_get_operations():
            operation_id = str(row.get("operationId") or "")
            if not operation_id:
                continue
            in_catalog = operation_id in allowlisted
            if in_catalog and not include_allowlisted:
                continue
            modes = suggested_display_modes(
                allowed_display_modes=None,
                meta_shape=str(row.get("metaShape") or ""),
            )
            items.append(
                {
                    **row,
                    "inCatalog": in_catalog,
                    "suggestedDisplayModes": modes,
                }
            )
        return items
