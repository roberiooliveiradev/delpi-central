from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def _use_case():
    return ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )


def test_build_heatmap_from_matrix_rows():
    presenter = ExternalActionResultPresenter()
    rows = [
        {"cliente": "Cliente A", "mes": "jan/2026", "valor": 10000},
        {"cliente": "Cliente A", "mes": "fev/2026", "valor": 12000},
        {"cliente": "Cliente B", "mes": "jan/2026", "valor": 8000},
        {"cliente": "Cliente B", "mes": "fev/2026", "valor": 9000},
    ]

    chart = presenter._try_heatmap_from_rows(rows)

    assert chart is not None
    assert chart["chartType"] == "heatmap"
    assert chart["config"]["xAxis"] == "mes"
    assert chart["config"]["yAxis"] == "cliente"
    assert chart["config"]["valueKey"] == "valor"
    assert len(chart["data"]) == 4


def test_build_stock_chart_from_nested_stock_items():
    presenter = ExternalActionResultPresenter()
    data = {
        "stock": {
            "items": [
                {
                    "branch": "01",
                    "warehouse": "01",
                    "current_quantity": 10,
                    "available_quantity": 8,
                    "committed_quantity": 2,
                },
                {
                    "branch": "02",
                    "warehouse": "01",
                    "current_quantity": 5,
                    "available_quantity": 5,
                    "committed_quantity": 0,
                },
            ]
        }
    }

    chart = presenter.build_chart_presentation(
        data,
        path="/products/10070014/stock",
        force=True,
    )

    assert chart is not None
    assert chart["type"] == "chart"
    assert chart["chartType"] == "horizontal_bar"
    assert len(chart["data"]) == 2


def test_presentation_metadata_nested_stock_schema_first():
    use_case = _use_case()
    meta = use_case._build_presentation_metadata(
        action={"path": "/products/{code}/stock"},
        sanitized_data={
            "stock": {
                "items": [
                    {
                        "branch": "01",
                        "warehouse": "01",
                        "current_quantity": 0,
                        "available_quantity": 0,
                        "committed_quantity": 0,
                    },
                    {
                        "branch": "02",
                        "warehouse": "99",
                        "current_quantity": 0,
                        "available_quantity": 0,
                        "committed_quantity": 0,
                    },
                ]
            }
        },
        resolved_path="/products/10070014/stock",
        request_parameters={},
    )

    assert meta.get("tablePresentation") or meta.get("textPresentation")
    assert meta.get("presentationDecision")


def test_presentation_metadata_flat_parents_schema_first():
    use_case = _use_case()
    meta = use_case._build_presentation_metadata(
        action={"path": "/products/{code}/parents"},
        sanitized_data={
            "product": {
                "code": "10070014",
                "description": "CABO",
                "type": "MP",
                "unit": "MT",
            },
            "parents": [
                {
                    "code": "P1",
                    "description": "CHICOTE 1",
                    "type": "PA",
                    "unit": "UN",
                    "quantity": 1,
                },
            ],
        },
        resolved_path="/products/10070014/parents",
        request_parameters={},
    )

    assert meta.get("tablePresentation") or meta.get("treePresentation") or meta.get("textPresentation")
    assert meta.get("presentationDecision")
