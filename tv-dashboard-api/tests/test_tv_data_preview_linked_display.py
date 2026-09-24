"""Preview editor must stamp linkedResolvedByBlockId for text/KPI paint."""

from tv_app.application.services.data.tv_data_preview_service import TvDataPreviewService


def test_preview_block_attaches_linked_text_display(monkeypatch):
    service = TvDataPreviewService()

    source = {
        "id": "src-1",
        "type": "data_source",
        "dataBinding": {"operationId": "op.demo", "params": {}},
    }
    text = {
        "id": "txt-1",
        "type": "text",
        "dataSourceId": "src-1",
        "textProjection": {
            "field": "forecast_value",
            "displayFormat": {"category": "currency", "currency": "BRL", "decimalPlaces": 2},
        },
        "frame": {"x": 0, "y": 0, "w": 10, "h": 5},
        "style": {},
        "content": "",
    }
    native = {"blocks": [source, text]}

    def fake_resolve(blocks, **kwargs):
        assert any(str(b.get("id")) == "txt-1" for b in blocks)
        return [
            {
                **source,
                "resolved": {
                    "kpi": {"value": 1234.5, "label": "x"},
                    "kpiMetrics": [{"field": "forecast_value", "value": 1234.5}],
                    "fields": [{"name": "forecast_value", "projectable": True}],
                    "serverDisplayApplied": True,
                },
            },
            {
                **text,
                "resolved": {
                    "kpi": {"value": 1234.5},
                    "kpiMetrics": [{"field": "forecast_value", "value": 1234.5}],
                    "displayText": "R$ 1.234,50",
                    "displayRuns": [{"text": "R$ 1.234,50"}],
                    "serverDisplayApplied": True,
                    "serverTextProjectionApplied": True,
                },
                "serverTextProjectionApplied": True,
            },
        ]

    monkeypatch.setattr(service._resolution, "resolve_blocks", fake_resolve)
    monkeypatch.setattr(
        "tv_app.application.services.data.tv_data_preview_service.validate_data_binding",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(service._catalog, "get_route", lambda *_a, **_k: {"operationId": "op.demo"})

    out = service.preview_block(source, native_config=native, authorization="Bearer x")
    linked = out["resolved"]["linkedResolvedByBlockId"]
    assert "txt-1" in linked
    assert linked["txt-1"]["displayText"] == "R$ 1.234,50"
    assert linked["txt-1"]["serverDisplayApplied"] is True


def test_blocks_for_preview_includes_text_and_views():
    source = {"id": "src-1", "type": "data_source", "dataBinding": {"operationId": "op"}}
    text = {"id": "t1", "type": "text", "dataSourceId": "src-1"}
    chart = {"id": "c1", "type": "chart_view", "dataSourceId": "src-1"}
    native = {"blocks": [source, text, chart, {"id": "img", "type": "image"}]}
    out = TvDataPreviewService._blocks_for_preview(source, native)
    ids = {str(b.get("id")) for b in out}
    assert ids >= {"src-1", "t1", "c1"}
    assert "img" not in ids
