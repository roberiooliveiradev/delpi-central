"""Sincroniza catálogo TV (tv_data_routes.json) a partir do OpenAPI live da api-delpi."""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import httpx
from delpi_auth.service_token import apply_internal_service_headers

from tv_app.application.services.tv_data_route_catalog_service import (
    reset_tv_data_route_catalog_cache,
    resolve_routes_path,
)
from tv_app.config import settings

logger = logging.getLogger(__name__)


def _generator_script_candidates() -> list[Path]:
    raw = str(os.getenv("TV_OPENAPI_GENERATOR_SCRIPT") or "").strip()
    paths: list[Path] = []
    if raw:
        paths.append(Path(raw))
    # Imagem Docker (COPY scripts → /app/tools)
    paths.append(Path("/app/tools/generate_tv_data_routes_from_openapi.py"))
    # Dev bind-mount monorepo / cwd típico
    here = Path(__file__).resolve()
    # …/tv-dashboard-api/tv_app/application/services/this.py → monorepo root = parents[4]
    paths.extend(
        [
            here.parents[4] / "scripts" / "generate_tv_data_routes_from_openapi.py",
            Path.cwd() / "scripts" / "generate_tv_data_routes_from_openapi.py",
        ]
    )
    return paths


def load_tv_routes_generator():
    for path in _generator_script_candidates():
        if not path.is_file():
            continue
        spec = importlib.util.spec_from_file_location(
            "generate_tv_data_routes_from_openapi",
            path,
        )
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, path
    raise FileNotFoundError(
        "Gerador TV ausente. Defina TV_OPENAPI_GENERATOR_SCRIPT ou copie "
        "scripts/generate_tv_data_routes_from_openapi.py para /app/tools/."
    )


def _overlays_path() -> Path:
    raw = str(os.getenv("TV_DATA_ROUTE_OVERLAYS_PATH") or "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parents[2] / "content" / "tv_data_route_overlays.json"


class TvOpenApiCatalogSyncService:
    """Fetch OpenAPI live → gera allowlist TV → grava JSON + limpa cache."""

    def fetch_live_openapi(self) -> dict[str, Any]:
        headers: dict[str, str] = {}
        apply_internal_service_headers(headers)
        caller = (settings.DELPI_API_CALLER_APP or "tv-dashboard-api").strip()
        if caller:
            headers["X-Delpi-Caller-App"] = caller
        base = (settings.DELPI_API_URL or "http://delpi-api-delpi:8000").rstrip("/")
        timeout = float(settings.TV_OPENAPI_SYNC_TIMEOUT_SECONDS or 45.0)
        with httpx.Client(base_url=base, timeout=timeout) as client:
            response = client.get("/openapi.json", headers=headers)
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict) or not isinstance(body.get("paths"), dict):
                raise ValueError("OpenAPI inválido (sem paths).")
            return body

    def sync_from_openapi_spec(
        self,
        spec: dict[str, Any],
        *,
        routes_path: Path | None = None,
        overlays_path: Path | None = None,
    ) -> dict[str, Any]:
        gen, script_path = load_tv_routes_generator()
        baseline_payload = gen.build_baseline_payload_from_openapi(spec)
        routes_target = routes_path or resolve_routes_path()
        overlays_target = overlays_path or _overlays_path()

        with tempfile.TemporaryDirectory(prefix="tv_openapi_sync_") as tmp:
            baseline_file = Path(tmp) / "baseline.json"
            baseline_file.write_text(
                json.dumps(baseline_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            generated = gen.generate_routes(
                baseline_path=baseline_file,
                routes_path=routes_target,
                overlays_path=overlays_target,
            )
            routes_target.parent.mkdir(parents=True, exist_ok=True)
            gen.write_routes(routes_target, generated)

        reset_tv_data_route_catalog_cache()
        report = {
            "ok": True,
            "routesWritten": len(generated),
            "operationCount": int(baseline_payload.get("operation_count") or 0),
            "routesPath": str(routes_target),
            "overlaysPath": str(overlays_target),
            "generatorScript": str(script_path),
            "source": "openapi_spec",
        }
        logger.info(
            "Catálogo TV sincronizado: %s rotas → %s",
            report["routesWritten"],
            report["routesPath"],
        )
        return report

    def sync_from_live_api(self) -> dict[str, Any]:
        spec = self.fetch_live_openapi()
        report = self.sync_from_openapi_spec(spec)
        report["source"] = "live_openapi"
        report["delpiApiUrl"] = (settings.DELPI_API_URL or "").rstrip("/")
        return report

    def sync_safe(self) -> dict[str, Any]:
        """Usado no startup — nunca derruba o processo."""
        try:
            return self.sync_from_live_api()
        except Exception as exc:  # noqa: BLE001 — startup resiliente
            logger.warning("Sync OpenAPI TV falhou (mantém catálogo atual): %s", exc)
            return {"ok": False, "error": str(exc)}
