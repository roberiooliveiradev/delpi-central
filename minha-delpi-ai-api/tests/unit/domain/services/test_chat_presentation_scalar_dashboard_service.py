from app.domain.services.chat_presentation_scalar_dashboard_service import (
    ChatPresentationScalarDashboardService,
)
from app.domain.services.chat_presentation_kpi_assembly_service import (
    ChatPresentationKpiAssemblyService,
)


def test_scalar_dashboard_builds_kpi_and_detail_table():
    payload = {
        "branch": "01",
        "gross_revenue": 14700.28,
        "rol": 12513.48,
        "icms": 911.75,
    }

    dashboard = ChatPresentationScalarDashboardService.build(
        payload,
        path="/financial/rol",
        build_kpi=lambda root, route: ChatPresentationKpiAssemblyService.build(
            title="Indicador Financeiro",
            cards=[
                {
                    "key": "rol",
                    "label": "ROL",
                    "value": root["rol"],
                    "color": "#0ea5e9",
                },
                {
                    "key": "gross_revenue",
                    "label": "Receita bruta",
                    "value": root["gross_revenue"],
                    "color": "#10b981",
                },
            ],
            min_cards=1,
        ),
        build_kv_table=lambda root, route: ChatPresentationScalarDashboardService.build_kv_table(
            root,
            path=route,
            label_for=lambda key: key,
            format_value=lambda key, value: str(value),
        ),
    )

    assert dashboard is not None
    assert dashboard["type"] == "dashboard"
    assert len(dashboard["panels"]) >= 1
    assert dashboard["panels"][0]["presentation"]["type"] == "kpi"

    if len(dashboard["panels"]) > 1:
        assert dashboard["panels"][1]["presentation"]["type"] == "table"
