"""Casos de regressão Playbook 09 — apresentação rica (P1–P15)."""

RICH_PRESENTATION_CASES = [
    {
        "id": "P1",
        "rows": [
            {"code": "10080001", "description": "Terminal", "stock": 50},
            {"code": "10080002", "description": "Conector", "stock": 12},
        ],
        "expected_selected": "table",
    },
    {
        "id": "P2",
        "rows": [
            {"month": "jan/2026", "value": 12000},
            {"month": "fev/2026", "value": 15000},
            {"month": "mar/2026", "value": 18000},
        ],
        "expected_selected": "line_chart",
    },
    {
        "id": "P3",
        "rows": [
            {"name": "Produto com nome bem longo A", "value": 40},
            {"name": "Produto com nome bem longo B", "value": 30},
            {"name": "Produto com nome bem longo C", "value": 20},
            {"name": "Produto com nome bem longo D", "value": 10},
            {"name": "Produto com nome bem longo E", "value": 8},
            {"name": "Produto com nome bem longo F", "value": 6},
            {"name": "Produto com nome bem longo G", "value": 4},
        ],
        "expected_selected": "horizontal_bar",
    },
    {
        "id": "P4",
        "rows": [
            {"client": "A", "value": 40},
            {"client": "B", "value": 35},
            {"client": "C", "value": 25},
        ],
        "user_message": "participação por cliente em rosca",
        "expected_selected": "donut",
    },
    {
        "id": "P5",
        "rows": [{"total": 125000}],
        "expected_selected": "kpi",
    },
    {
        "id": "P6",
        "rows": [
            {"code": "10080001", "children": [{"code": "COMP-1"}]},
        ],
        "expected_selected": "tree",
    },
    {
        "id": "P7",
        "rows": [],
        "user_message": "coloque o relatório na lousa",
        "expected_selected": "canvas",
    },
    {
        "id": "P8",
        "rows": [],
        "user_message": "monte um plano de ação com pendências",
        "expected_selected": "checklist",
    },
    {
        "id": "P9",
        "rows": [
            {"name": f"Item {index}", "value": index}
            for index in range(1, 12)
        ],
        "expected_selected": "horizontal_bar",
    },
    {
        "id": "P10",
        "rows": [
            {"status": "ativo", "owner": "Compras"},
            {"status": "pendente", "owner": "Engenharia"},
        ],
        "expected_selected": "table",
    },
    {
        "id": "P11",
        "rows": [
            {"grupo": "Linha A", "meta": 100, "realizado": 110},
            {"grupo": "Linha B", "meta": 100, "realizado": 95},
        ],
        "user_message": "compare meta versus realizado",
        "expected_selected": "grouped_bar",
    },
    {
        "id": "P12",
        "rows": [
            {"month": "jan", "value": 10},
            {"month": "fev", "value": 12},
        ],
        "user_preference": "chart",
        "expected_selected": "chart",
    },
    {
        "id": "P13",
        "rows": [
            {"month": "jan", "value": 10},
            {"month": "fev", "value": 12},
        ],
        "user_preference": "table",
        "expected_selected": "table",
    },
    {
        "id": "P14",
        "rows": [],
        "expected_selected": "text",
    },
    {
        "id": "P15",
        "rows": [
            {"month": "jan", "value": 10},
            {"month": "fev", "value": 12},
        ],
        "user_message": "mostre em gráfico de linha",
        "expected_selected": "line_chart",
    },
]
