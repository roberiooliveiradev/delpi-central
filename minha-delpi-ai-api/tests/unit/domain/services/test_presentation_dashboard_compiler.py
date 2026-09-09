"""Unit tests — PresentationDashboardCompilerService."""

from __future__ import annotations

from app.domain.entities.presentation_spec import (
    PresentationDashboardPanelSpec,
    PresentationDashboardSpec,
    PresentationSpec,
)
from app.domain.services.presentation_compilers.presentation_dashboard_compiler_service import (
    PresentationDashboardCompilerService,
)


def test_dashboard_compiler_reorders_and_filters_panels_from_existing_slots():
    spec = PresentationSpec(
        view="dashboard",
        dashboard=PresentationDashboardSpec(
            panels=(
                PresentationDashboardPanelSpec(
                    id="table-main",
                    presentation="table",
                    role="operational",
                    fields=("product_code", "planned_qty"),
                ),
                PresentationDashboardPanelSpec(
                    id="kpi-top",
                    presentation="kpi",
                    role="summary",
                    measures=("planned_qty",),
                ),
                PresentationDashboardPanelSpec(
                    id="chart-trend",
                    presentation="chart",
                    role="trend",
                ),
            )
        ),
    )
    metadata = {
        "kpiPresentation": {
            "type": "kpi",
            "title": "Resumo",
            "cards": [
                {"key": "planned_qty", "label": "Qtd", "value": 35},
                {"key": "balance", "label": "Saldo", "value": 100},
            ],
        },
        "tablePresentation": {
            "type": "table",
            "columns": [
                {"key": "product_code"},
                {"key": "warehouse"},
                {"key": "planned_qty"},
            ],
            "rows": [{"product_code": "P1", "warehouse": "W1", "planned_qty": 10}],
        },
        "chartPresentation": {
            "type": "chart",
            "chartType": "bar",
            "data": [{"product_code": "P1", "planned_qty": 10}],
            "config": {},
        },
        "presentationDecision": {},
    }
    PresentationDashboardCompilerService.apply(metadata, spec=spec)

    dashboard = metadata["dashboardPresentation"]
    assert dashboard["type"] == "dashboard"
    assert [panel["id"] for panel in dashboard["panels"]] == [
        "table-main",
        "kpi-top",
        "chart-trend",
    ]
    assert dashboard["config"]["bindingProvenance"] == "COMPILED"
    assert metadata["presentationDecision"]["selected"] == "dashboard"

    table_panel = dashboard["panels"][0]["presentation"]
    assert {col["key"] for col in table_panel["columns"]} == {
        "product_code",
        "planned_qty",
    }
    kpi_panel = dashboard["panels"][1]["presentation"]
    assert len(kpi_panel["cards"]) == 1
    assert kpi_panel["cards"][0]["key"] == "planned_qty"


def test_dashboard_compiler_sets_unmet_intent_for_invalid_panel():
    spec = PresentationSpec(
        view="dashboard",
        dashboard=PresentationDashboardSpec(
            panels=(
                PresentationDashboardPanelSpec(
                    id="missing-kpi",
                    presentation="kpi",
                    measures=("ghost",),
                ),
            )
        ),
    )
    metadata = {
        "tablePresentation": {
            "type": "table",
            "columns": [{"key": "product_code"}],
            "rows": [{"product_code": "P1"}],
        },
        "presentationDecision": {},
    }
    PresentationDashboardCompilerService.apply(metadata, spec=spec)
    assert metadata.get("dashboardPresentation") is None
    assert metadata["presentationDecision"]["unmetIntent"] == "dashboard_not_materializable"
