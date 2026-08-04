"""Fingerprint: preview-block ≡ resolve_blocks (present) para o mesmo slide/defaults."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tv_app.application.services.comunicado_data_enrichment_service import (
    ComunicadoDataEnrichmentService,
    reset_comunicado_data_block_cache,
)
from tv_app.application.services.data.slide_data_resolution_service import (
    SlideDataResolutionService,
)
from tv_app.application.services.data.tv_data_preview_service import TvDataPreviewService
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService


def _department_indicators_payload(*, idd: float = 6.57) -> dict:
    return {
        "meta": {
            "operationId": "get_dashboard_department_indicators",
            "shape": "playbook_report",
        },
        "data": {
            "item": {
                "department_id": "quality",
                "idd": idd,
                "score": idd,
                "indicators": [
                    {"name": "PPM externo", "score": 10},
                    {"name": "Refugo", "score": 0.84},
                    {"name": "Retrabalho", "score": 0.22},
                ],
            }
        },
        "route": {
            "label": "Departamento — IDD, metas e realizado",
            "valueFields": ["idd", "score"],
            "tableFields": "indicators",
            "allowedDisplayModes": ["kpi", "table", "auto"],
            "tvConstraints": {"maxRows": 20},
        },
    }


def _kpi_fingerprint(resolved: dict | None) -> tuple:
    if not isinstance(resolved, dict):
        return ()
    metrics = resolved.get("kpiMetrics") or []
    metric_pairs = tuple(
        (str(item.get("field") or ""), item.get("value"))
        for item in metrics
        if isinstance(item, dict)
    )
    kpi = resolved.get("kpi") if isinstance(resolved.get("kpi"), dict) else {}
    return (kpi.get("value"), metric_pairs)


@pytest.fixture
def quality_slide_blocks():
    source = {
        "id": "src-quality",
        "type": "data_source",
        "dataBinding": {
            "operationId": "get_dashboard_department_indicators",
            "displayMode": "kpi",
            "params": {"department_id": "quality"},
        },
    }
    text = {
        "id": "idd-chip",
        "type": "text",
        "content": "IDD —",
        "dataSourceId": "src-quality",
        "textProjection": {
            "field": "score",
            "format": "number",
            "decimalPlaces": 2,
            "prefix": "IDD ",
        },
        "frame": {"x": 0, "y": 0, "w": 20, "h": 10},
    }
    return source, text


def test_preview_block_and_present_resolve_share_idd_fingerprint(quality_slide_blocks):
    """Mesmo native_config + defaults → mesmo KPI IDD no preview e no enrich present."""
    reset_comunicado_data_block_cache()
    source, text = quality_slide_blocks
    catalog = TvDataRouteCatalogService()
    if not catalog.get_route("get_dashboard_department_indicators"):
        pytest.skip("Catálogo department indicators indisponível")

    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = _department_indicators_payload(idd=6.57)
    enrichment = ComunicadoDataEnrichmentService(catalog=catalog, gateway=gateway)
    resolution = SlideDataResolutionService(catalog=catalog, enrichment=enrichment)
    preview = TvDataPreviewService(
        catalog=catalog,
        enrichment=enrichment,
        resolution=resolution,
    )

    native_config = {
        "blocks": [source, text],
        "dataFilters": {"department_id": "quality", "dateRangePreset": "this_month"},
    }
    playlist_defaults = {"branch": "01"}

    previewed = preview.preview_block(
        dict(source),
        native_config=native_config,
        playlist_defaults=playlist_defaults,
        authorization="Bearer editor",
        user=object(),
        force_refresh=True,
    )
    present_blocks = resolution.resolve_blocks(
        [dict(source), dict(text)],
        cfg=native_config,
        playlist_defaults=playlist_defaults,
        authorization=None,
        user=None,
        force_refresh=True,
    )
    present_source = next(b for b in present_blocks if b.get("id") == "src-quality")
    present_text = next(b for b in present_blocks if b.get("id") == "idd-chip")

    assert _kpi_fingerprint(previewed.get("resolved")) == _kpi_fingerprint(
        present_source.get("resolved")
    )
    assert present_source.get("resolved", {}).get("kpi", {}).get("value") == 6.57
    assert present_text.get("resolved", {}).get("kpi", {}).get("value") == 6.57
    assert present_text.get("serverTextProjectionApplied") is True


def test_notify_presentation_changed_clears_data_cache(monkeypatch):
    """Save/WS presentation_updated invalida TTL — present não serve IDD stale."""
    from tv_app.application.services import presentation_change_notifier as notifier

    calls: list[str] = []

    def _reset() -> None:
        calls.append("reset")

    monkeypatch.setattr(
        "tv_app.application.services.comunicado_data_enrichment_service.reset_comunicado_data_block_cache",
        _reset,
    )
    monkeypatch.setattr(
        notifier.presentation_realtime_hub,
        "schedule_broadcast",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        notifier,
        "build_presentation_content_revision",
        lambda *_a, **_k: "rev-1",
    )

    notifier.notify_presentation_changed(playlist_id="00000000-0000-0000-0000-000000000001", reason="slide_saved")
    assert calls == ["reset"]
