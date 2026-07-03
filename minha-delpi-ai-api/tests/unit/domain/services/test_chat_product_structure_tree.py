from app.domain.services.chat_product_structure_presentation_service import (
    ChatProductStructurePresentationService,
)


def _sample_structure_payload():
    return {
        "root": {
            "code": "90260148",
            "description": "CHICOTE DE LIGACAO",
            "type": "PA",
            "unit": "MI",
            "quantity": 1,
        },
        "items": [
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
                    },
                ],
            },
        ],
        "total": 1,
    }


def _sample_parents_payload():
    return {
        "root": {
            "code": "10030015",
            "description": "CABO EPR",
            "type": "MP",
            "unit": "MT",
            "quantity": 1,
        },
        "items": [
            {
                "code": "50220013",
                "description": "CB18BRAN",
                "type": "PI",
                "unit": "MI",
                "quantity": 368.0,
                "parents": [
                    {
                        "code": "90260148",
                        "description": "CHICOTE DE LIGACAO",
                        "type": "PA",
                        "unit": "MI",
                        "quantity": 2.0,
                        "parents": [],
                    }
                ],
            }
        ],
        "total": 1,
    }


def test_build_tree_presentation_for_structure():
    tree = ChatProductStructurePresentationService.build_tree_presentation(
        _sample_structure_payload(),
        path="/products/90260148/structure",
    )

    assert tree is not None
    assert tree["type"] == "tree"
    assert tree["title"] == "Estrutura do produto 90260148"
    assert tree["root"]["label"] == "90260148"
    assert tree["root"]["children"][0]["label"] == "50220013"
    assert tree["root"]["children"][0]["children"][0]["label"] == "10030015"


def test_build_tree_presentation_for_analyser():
    payload = {"product": {"code": "90260148"}, "structure": _sample_structure_payload()}

    tree = ChatProductStructurePresentationService.build_tree_presentation(
        payload,
        path="/products/90260148/analyser",
    )

    assert tree is not None
    assert tree["type"] == "tree"
    assert tree["root"]["children"][0]["badge"] == "PI"


def test_build_tree_presentation_for_parents():
    tree = ChatProductStructurePresentationService.build_tree_presentation(
        _sample_parents_payload(),
        path="/products/10030015/parents",
    )

    assert tree is not None
    assert tree["type"] == "tree"
    assert tree["title"] == "Onde é usado o produto 10030015"
    assert tree["root"]["children"][0]["label"] == "50220013"
    assert tree["root"]["children"][0]["children"][0]["label"] == "90260148"


def test_build_tree_presentation_for_flat_product_parents_payload():
    tree = ChatProductStructurePresentationService.build_tree_presentation(
        {
            "product": {
                "code": "10070014",
                "description": "CABO PP",
                "type": "MP",
                "unit": "MT",
                "quantity": 1,
            },
            "parents": [
                {
                    "code": "90260148",
                    "description": "CHICOTE",
                    "type": "PA",
                    "unit": "UN",
                    "quantity": 1,
                    "parents": [],
                },
            ],
        },
        path="/products/10070014/parents",
    )

    assert tree is not None
    assert tree["type"] == "tree"
    assert tree["root"]["label"] == "10070014"
    assert tree["root"]["children"][0]["label"] == "90260148"


def test_build_tree_presentation_for_structure_exclusivity_fixture():
    from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta

    envelope = load_api_delpi_fixture_with_meta("product_structure_exclusivity_90261805.json")

    tree = ChatProductStructurePresentationService.build_tree_presentation(
        envelope,
        path="/products/90261805/structure/exclusivity",
    )

    assert tree is not None
    assert tree["type"] == "tree"
    assert tree["root"]["label"] == "90261805"
    assert tree["root"]["children"][0]["label"] == "50222613"
    mp_nodes = tree["root"]["children"][0]["children"]
    assert len(mp_nodes) == 2
    assert {node["label"] for node in mp_nodes} == {"10020053", "10080185"}


def test_build_tree_presentation_for_structure_exclusivity_legacy_fixture():
    from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta

    envelope = load_api_delpi_fixture_with_meta("product_structure_exclusivity_90269002.json")

    tree = ChatProductStructurePresentationService.build_tree_presentation(
        envelope,
        path="/products/90269002/structure/exclusivity",
    )

    assert tree is not None
    assert tree["type"] == "tree"
    assert tree["root"]["label"] == "90269002"
    assert tree["root"]["children"][0]["label"] == "50219001"
    assert tree["root"]["children"][0]["children"][0]["label"] == "10019001"
    assert tree["root"]["children"][0]["children"][0]["meta"]["exclusive_raw_material"] == "Sim"
