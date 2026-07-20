"""Testes do sync OpenAPI → catálogo TV."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from tv_app.application.services.tv_openapi_catalog_sync_service import (
    TvOpenApiCatalogSyncService,
    load_tv_routes_generator,
)


MINI_OPENAPI = {
    "openapi": "3.1.0",
    "info": {"title": "api-delpi", "version": "1.0"},
    "paths": {
        "/commercial/kpi": {
            "get": {
                "operationId": "get_commercial_kpi_demo",
                "summary": "Demo KPI",
                "tags": ["Comercial"],
                "parameters": [
                    {
                        "name": "branch",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string", "enum": ["01", "02"]},
                    }
                ],
                "x-delpi": {
                    "shape": "scalar",
                    "category": "commercial",
                    "locale": {
                        "pt-BR": {
                            "summary": "KPI demo",
                            "whenToUse": "Teste",
                            "label": "KPI demo",
                        }
                    },
                },
            }
        },
        "/health": {
            "get": {
                "operationId": "get_health",
                "summary": "Health",
                "tags": ["Health"],
            }
        },
    },
}


def test_load_generator_from_monorepo() -> None:
    module, path = load_tv_routes_generator()
    assert path.name == "generate_tv_data_routes_from_openapi.py"
    assert hasattr(module, "build_baseline_payload_from_openapi")
    assert hasattr(module, "generate_routes")


def test_build_baseline_from_openapi_extracts_get_and_x_delpi() -> None:
    gen, _ = load_tv_routes_generator()
    payload = gen.build_baseline_payload_from_openapi(MINI_OPENAPI)
    assert payload["operation_count"] == 2
    by_id = {row["operationId"]: row for row in payload["operations"]}
    assert by_id["get_commercial_kpi_demo"]["method"] == "GET"
    assert by_id["get_commercial_kpi_demo"]["parameters"][0]["name"] == "branch"
    assert by_id["get_commercial_kpi_demo"]["xDelpi"]["shape"] == "scalar"
    assert by_id["get_commercial_kpi_demo"]["xDelpi"]["locale"]["pt-BR"]["label"] == "KPI demo"


def test_sync_from_openapi_spec_writes_routes(tmp_path: Path) -> None:
    routes_path = tmp_path / "tv_data_routes.json"
    overlays_path = tmp_path / "overlays.json"
    overlays_path.write_text(
        json.dumps({"version": 1, "overlays": {}}, ensure_ascii=False),
        encoding="utf-8",
    )
    # Seed mínimo para merge existing
    routes_path.write_text(json.dumps({"routes": []}, ensure_ascii=False), encoding="utf-8")

    service = TvOpenApiCatalogSyncService()
    with patch(
        "tv_app.application.services.tv_openapi_catalog_sync_service.reset_tv_data_route_catalog_cache"
    ) as mock_reset:
        report = service.sync_from_openapi_spec(
            MINI_OPENAPI,
            routes_path=routes_path,
            overlays_path=overlays_path,
        )
    assert report["ok"] is True
    assert report["routesWritten"] >= 2
    mock_reset.assert_called_once()
    stored = json.loads(routes_path.read_text(encoding="utf-8"))
    ops = {r["operationId"] for r in stored["routes"]}
    assert "get_commercial_kpi_demo" in ops
    assert "get_health" in ops


def test_sync_safe_returns_error_without_raising() -> None:
    service = TvOpenApiCatalogSyncService()
    with patch.object(service, "sync_from_live_api", side_effect=RuntimeError("down")):
        report = service.sync_safe()
    assert report["ok"] is False
    assert "down" in report["error"]


def test_generator_cli_from_openapi(tmp_path: Path) -> None:
    gen, script = load_tv_routes_generator()
    openapi_file = tmp_path / "openapi.json"
    openapi_file.write_text(json.dumps(MINI_OPENAPI), encoding="utf-8")
    baseline_out = tmp_path / "baseline.json"
    routes_out = tmp_path / "routes.json"
    overlays = tmp_path / "overlays.json"
    overlays.write_text(json.dumps({"overlays": {}}), encoding="utf-8")
    routes_out.write_text(json.dumps({"routes": []}), encoding="utf-8")

    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--from-openapi",
            str(openapi_file),
            "--baseline-out",
            str(baseline_out),
            "--routes",
            str(routes_out),
            "--overlays",
            str(overlays),
            "--write",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert baseline_out.is_file()
    assert json.loads(routes_out.read_text(encoding="utf-8"))["routes"]
