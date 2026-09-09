"""Contract: PresentationSpec JSON Schema is closed (additionalProperties false)."""

from app.domain.entities.presentation_spec import (
    PRESENTATION_INTENT_JSON_SCHEMA,
    PRESENTATION_SPEC_JSON_SCHEMA,
    SUPPORTED_VIEWS,
    PresentationDashboardSpec,
    PresentationDashboardPanelSpec,
    PresentationDeliverySpec,
    PresentationKpiSpec,
    PresentationSpec,
    PresentationTableSpec,
    PresentationTextSpec,
    PresentationTreeSpec,
)


def test_presentation_spec_schema_is_closed():
    assert PRESENTATION_SPEC_JSON_SCHEMA["additionalProperties"] is False
    assert PRESENTATION_SPEC_JSON_SCHEMA["required"] == ["version", "view"]
    encoding = PRESENTATION_SPEC_JSON_SCHEMA["properties"]["encoding"]
    assert encoding["additionalProperties"] is False


def test_presentation_intent_schema_is_closed():
    assert PRESENTATION_INTENT_JSON_SCHEMA["additionalProperties"] is False


def test_dashboard_is_supported_view():
    assert "dashboard" in SUPPORTED_VIEWS
    assert "dashboard" in PRESENTATION_SPEC_JSON_SCHEMA["properties"]["view"]["enum"]


def test_flat_v1_roundtrip_preserved():
    """Positive: fixtures flat v1 (pré-nested) continuam válidas."""
    payload = {
        "version": 1,
        "view": "chart",
        "mark": "heatmap",
        "encoding": {
            "x": {"field": "product_code"},
            "y": {"field": "branch"},
            "color": {"field": "balance"},
        },
        "fields": [{"field": "product_code"}, {"field": "branch"}, {"field": "balance"}],
        "sort": {"field": "balance", "direction": "desc"},
        "labels": {"balance": "Saldo"},
        "formats": {"balance": "quantity"},
        "paletteFamily": "sequential-blue",
        "legend": {"visible": True},
        "provenance": "DETERMINISTIC",
    }
    spec = PresentationSpec.from_dict(payload)
    assert spec is not None
    assert spec.view == "chart"
    assert spec.mark == "heatmap"
    assert spec.sort_field == "balance"
    assert spec.palette_family == "sequential-blue"
    assert spec.table is None
    assert spec.dashboard is None
    roundtrip = PresentationSpec.from_dict(spec.as_dict())
    assert roundtrip is not None
    assert roundtrip.as_dict() == spec.as_dict()


def test_nested_dashboard_roundtrip():
    """Sibling: Spec nested multi-view (dashboard + delivery)."""
    payload = {
        "version": 1,
        "view": "dashboard",
        "provenance": "COMPOSER",
        "dashboard": {
            "panels": [
                {
                    "id": "kpi-top",
                    "presentation": "kpi",
                    "role": "summary",
                    "measures": ["balance"],
                },
                {
                    "id": "chart-main",
                    "presentation": "chart",
                    "fields": ["product_code", "balance"],
                },
                {"id": "table-detail", "presentation": "table", "fields": ["product_code"]},
            ]
        },
        "delivery": {"preferCanvas": False},
        "kpi": {"measureFields": ["balance"], "cardOrder": ["balance"], "tones": ["neutral"]},
        "table": {"density": "compact", "hiddenFields": ["unit"]},
        "text": {"sectionPlan": ["summary", "highlights"], "proseDensity": "compact"},
        "tree": {"levelFields": ["branch", "product_code"], "maxDepth": 2},
    }
    spec = PresentationSpec.from_dict(payload)
    assert spec is not None
    assert spec.view == "dashboard"
    assert isinstance(spec.dashboard, PresentationDashboardSpec)
    assert len(spec.dashboard.panels) == 3
    assert isinstance(spec.dashboard.panels[0], PresentationDashboardPanelSpec)
    assert spec.dashboard.panels[0].presentation == "kpi"
    assert isinstance(spec.kpi, PresentationKpiSpec)
    assert isinstance(spec.table, PresentationTableSpec)
    assert spec.table.density == "compact"
    assert isinstance(spec.text, PresentationTextSpec)
    assert isinstance(spec.tree, PresentationTreeSpec)
    assert isinstance(spec.delivery, PresentationDeliverySpec)
    assert spec.delivery.prefer_canvas is False
    assert "dashboard" in spec.as_dict()
    assert PresentationSpec.from_dict(spec.as_dict()).as_dict() == spec.as_dict()


def test_nested_schema_blocks_are_closed():
    """Negative: nested blocks declarados no schema com additionalProperties false."""
    props = PRESENTATION_SPEC_JSON_SCHEMA["properties"]
    for key in ("table", "chart", "kpi", "tree", "dashboard", "text", "delivery"):
        assert key in props
        assert props[key]["additionalProperties"] is False
    panel_schema = props["dashboard"]["properties"]["panels"]["items"]
    assert panel_schema["additionalProperties"] is False
    assert set(panel_schema["properties"]["presentation"]["enum"]) == {
        "kpi",
        "chart",
        "table",
    }


def test_from_dict_ignores_empty_nested_blocks():
    """Negative: blocos vazios / inválidos não materializam nested."""
    spec = PresentationSpec.from_dict(
        {
            "version": 1,
            "view": "table",
            "table": {},
            "dashboard": {"panels": [{"id": "", "presentation": "kpi"}]},
            "delivery": {},
        }
    )
    assert spec is not None
    assert spec.table is None
    assert spec.dashboard is not None
    assert spec.dashboard.panels == ()
    assert spec.delivery is None
