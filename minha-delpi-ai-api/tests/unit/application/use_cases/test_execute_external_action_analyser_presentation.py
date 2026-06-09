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
                            "components": [
                                {
                                    "code": "10030015",
                                    "description": "CABO EPR 130ºC 18AWG BN NBR 9114",
                                    "type": "MP",
                                    "unit": "MT",
                                    "quantity": 368.0,
                                    "components": [],
                                },
                                {
                                    "code": "10080031",
                                    "description": "TERM. FASTON 6,30X0,80",
                                    "type": "MP",
                                    "unit": "PC",
                                    "quantity": 1000.0,
                                    "components": [],
                                },
                            ],
                        },
                        {
                            "code": "50220015",
                            "description": "CB18VERM-00318/06/15-3100-0000",
                            "type": "PI",
                            "unit": "MI",
                            "quantity": 2.0,
                            "components": [
                                {
                                    "code": "10030012",
                                    "description": "CABO EPR 130ºC 18AWG VM NBR 9114",
                                    "type": "MP",
                                    "unit": "MT",
                                    "quantity": 318.0,
                                    "components": [],
                                },
                                {
                                    "code": "10080031",
                                    "description": "TERM. FASTON 6,30X0,80",
                                    "type": "MP",
                                    "unit": "PC",
                                    "quantity": 1000.0,
                                    "components": [],
                                },
                            ],
                        },
                    ],
                },
            },
            "guide": {
                "success": True,
                "total": 0,
                "data": [],
            },
            "inspection": {
                "success": True,
                "total": 7,
                "data": [
                    {
                        "product": "90260148",
                        "parentCode": None,
                        "level": 0,
                        "QP6": None,
                        "QP7": None,
                        "QP8": None,
                    },
                    {
                        "product": "50220013",
                        "parentCode": "90260148",
                        "level": 1,
                        "QP6": None,
                        "QP7": None,
                        "QP8": None,
                    },
                ],
            },
        },
    }


def test_normalize_raw_analyser_payload_enables_tree_and_structure_table():
    presenter = ExternalActionResultPresenter()
    root = presenter._normalize_analyser_root(
        presenter._unwrap_data(_raw_analyser_api_payload()),
    )

    tree = presenter.build_tree_presentation(root, path="/products/90260148/analyser")
    tables = presenter.build_analyser_auxiliary_table_presentations(root)
    titles = [str(table.get("title") or "") for table in tables]

    assert tree is not None
    assert tree["type"] == "tree"
    assert any("estrutura" in title.lower() for title in titles)


def test_analyser_presentation_metadata_includes_tree_and_auxiliary_tables():
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

    primary = metadata.get("presentation") or metadata.get("treePresentation")

    assert primary is not None
    assert primary["type"] == "tree"
    assert primary["root"]["label"] == "90260148"
    assert primary["root"]["children"][0]["label"] == "50220013"

    tables = list(metadata.get("tablePresentations") or [])

    for key in ("inspectionTablePresentation", "profileTablePresentation", "tablePresentation"):
        slot = metadata.get(key)

        if isinstance(slot, dict) and slot.get("type") == "table":
            tables.append(slot)

    titles = [str(table.get("title") or "") for table in tables]

    assert any(title.startswith("Produto ") for title in titles)

    plan = metadata.get("stackPresentationPlan") or {}
    visibility = plan.get("sectionVisibility") or {}

    assert visibility.get("structure") is True
    assert "tree" in (plan.get("tailVisualOrder") or [])
    assert not any("componentes da estrutura" in title.lower() for title in titles)
