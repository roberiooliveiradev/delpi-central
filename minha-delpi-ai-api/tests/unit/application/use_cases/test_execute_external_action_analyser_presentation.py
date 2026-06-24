from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def _raw_analyser_api_payload():
    """Envelope bruto da API (data + components) — sem root/items normalizados."""
    return {
        "success": True,
        "message": "Análise completa de 90260148 retornada com sucesso.",
        "data": {
            "success": True,
            "product": {
                "success": True,
                "data": {
                    "group_code": "9026",
                    "code": "90260148",
                    "description": "CHICOTE DE LIGACAO",
                    "type": "PA",
                    "unit": "MI",
                    "active": "S",
                    "blocked": "2",
                    "customer_reference": "3E 4270 G02",
                    "default_warehouse": "01",
                    "last_purchase_price": 0.0,
                    "standard_cost": 272.8,
                    "last_revision_date": "20031031",
                    "ncm_ipi_position": "85444200",
                },
            },
            "structure": {
                "success": True,
                "total": 2,
                "data": {
                    "code": "90260148",
                    "description": "CHICOTE DE LIGACAO",
                    "type": "PA",
                    "unit": "MI",
                    "quantity": 1.0,
                    "components": [
                        {
                            "code": "50220013",
                            "description": "CB18BRAN-00368/06/15-3100-0000",
                            "type": "PI",
                            "unit": "MI",
                            "quantity": 2.0,
                            "components": [],
                        },
                    ],
                },
            },
            "guide": {"success": True, "total": 0, "data": []},
            "inspection": {
                "success": True,
                "total": 1,
                "data": [
                    {
                        "product": "90260148",
                        "parentCode": None,
                        "level": 0,
                    },
                ],
            },
        },
    }


def test_normalize_raw_analyser_payload_schema_first_tree():
    presenter = ExternalActionResultPresenter()
    root = presenter._normalize_analyser_root(
        presenter._unwrap_data(_raw_analyser_api_payload()),
    )

    visual = presenter.build_presentation(
        _raw_analyser_api_payload(),
        path="/products/90260148/analyser",
    )

    assert visual is not None
    assert visual.get("type") in {"tree", "table", "markdown", "kpi"}
    assert root.get("structure")


def test_analyser_presentation_metadata_schema_first():
    use_case = ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )

    metadata = use_case._build_presentation_metadata(
        action={"path": "/products/{code}/analyser"},
        sanitized_data=_raw_analyser_api_payload(),
        resolved_path="/products/90260148/analyser",
        request_parameters={},
    )

    assert metadata.get("presentationDecision")
    assert (
        metadata.get("treePresentation")
        or metadata.get("tablePresentation")
        or metadata.get("textPresentation")
    )
