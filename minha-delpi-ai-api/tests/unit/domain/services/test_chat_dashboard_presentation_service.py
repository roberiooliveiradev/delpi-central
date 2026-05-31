from app.domain.services.chat_dashboard_presentation_service import (
    ChatDashboardPresentationService,
)


def _fake_kpi(summary, path):
    return {
        "type": "kpi",
        "title": "Resumo LMP",
        "cards": [{"label": "Total", "value": summary.get("total_items", 0)}],
    }


def _fake_lmp_table(items, root):
    return {
        "type": "table",
        "title": f"LMPs ({len(items)})",
        "columns": [{"key": "sale_number", "label": "OV"}],
        "rows": items,
    }


def test_build_lmp_dashboard_multi_panel():
    root = {
        "summary": {
            "total_items": 12,
            "percent_dentro_prazo": 75.5,
            "avg_lead_time": 4.2,
        },
        "charts": {
            "levelData": [
                {"name": "Nível 1", "value": 5},
                {"name": "Nível 2", "value": 7},
            ],
            "statusData": [
                {"name": "No prazo", "value": 8},
                {"name": "Atrasado", "value": 4},
            ],
        },
        "items": [
            {
                "sale_number": "OV001",
                "branch": "01",
                "listing_kind": "LMP",
                "status": "No prazo",
                "sale_description": "Projeto A",
            }
        ],
        "total": 1,
    }

    dashboard = ChatDashboardPresentationService.build(
        root,
        path="/engineering/lmps/dashboard",
        build_kpi=_fake_kpi,
        build_lmp_table=_fake_lmp_table,
        build_items_table=lambda items, title: None,
    )

    assert dashboard is not None
    assert dashboard["type"] == "dashboard"
    assert len(dashboard["panels"]) >= 3
    assert dashboard["panels"][0]["presentation"]["type"] == "kpi"


def test_skips_single_panel():
    root = {
        "summary": {"total_items": 1},
    }

    dashboard = ChatDashboardPresentationService.build(
        root,
        path="/engineering/lmps/dashboard",
        build_kpi=_fake_kpi,
        build_lmp_table=_fake_lmp_table,
        build_items_table=lambda items, title: None,
    )

    assert dashboard is None
