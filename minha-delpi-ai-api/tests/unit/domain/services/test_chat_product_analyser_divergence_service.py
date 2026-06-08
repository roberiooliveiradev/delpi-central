from app.domain.services.chat_product_analyser_divergence_service import (
    ChatProductAnalyserDivergenceService,
)


def _root_with_cross_collection_gap():
    return {
        "product": {
            "code": "90260114",
            "description": "CHICOTE DE LIGACAO",
            "type": "PA",
            "group_code": "9026",
        },
        "guide": {"items": [], "total": 0},
        "inspection": {
            "items": [
                {
                    "product": "10080034",
                    "level": 1,
                    "QP6": [],
                    "QP7": [],
                    "QP8": [],
                },
            ],
            "total": 1,
        },
        "structure": {
            "items": [
                {
                    "code": "50212194",
                    "components": [
                        {"code": "50212194", "description": "CB20PRET", "type": "PI"},
                    ],
                }
            ],
            "total": 1,
        },
    }


def test_attention_points_cover_empty_guide_and_inspection_gap():
    root = _root_with_cross_collection_gap()
    product = root["product"]

    points = ChatProductAnalyserDivergenceService.build_attention_points(root, product)

    assert any("roteiro" in point.lower() for point in points)
    assert any("10080034" in point for point in points)
    assert any("QP6" in point or "qp" in point.lower() for point in points)


def test_attention_points_when_inspection_not_registered():
    root = {
        "product": {
            "code": "90260015",
            "description": "CHICOTE DE LIGACAO",
            "type": "PA",
            "group_code": "9026",
        },
        "guide": {"items": [{"product_code": "90260015", "operation_description": "EMBALAR"}], "total": 1},
        "inspection": {"items": [], "total": 0},
        "structure": {
            "items": [
                {
                    "code": "50210372",
                    "components": [
                        {"code": "10420040", "description": "CABO", "type": "MP"},
                    ],
                }
            ],
            "total": 1,
        },
    }
    product = root["product"]

    points = ChatProductAnalyserDivergenceService.build_attention_points(root, product)

    assert any("inspeção" in point.lower() and "não cadastrad" in point.lower() for point in points)


def test_attention_points_when_inspection_collection_missing():
    root = {
        "product": {"code": "90260015", "description": "ITEM", "type": "PA"},
        "guide": {"items": [{"product_code": "90260015", "operation_description": "OP"}], "total": 1},
        "structure": {"items": [], "total": 0},
    }

    points = ChatProductAnalyserDivergenceService.build_attention_points(
        root,
        root["product"],
    )

    assert any("inspeção" in point.lower() and "não cadastrad" in point.lower() for point in points)


def test_opening_narrative_mentions_composition_and_sources():
    root = _root_with_cross_collection_gap()
    product = root["product"]

    narrative = ChatProductAnalyserDivergenceService.build_opening_narrative(root, product)

    assert narrative is not None
    assert "90260114" in narrative
    assert "CB20PRET" in narrative or "50212194" in narrative
