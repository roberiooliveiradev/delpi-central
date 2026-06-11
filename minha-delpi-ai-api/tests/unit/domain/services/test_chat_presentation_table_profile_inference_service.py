from app.domain.services.chat_presentation_table_profile_inference_service import (
    ChatPresentationTableProfileInferenceService,
)


def test_infer_profile_name_from_entity_hint():
    profile = ChatPresentationTableProfileInferenceService.infer_profile_name(
        path="/products/90261255/cost-impact-simulation",
        entity="product_cost_impact_simulation",
        sample_row={"raw_material_code": "10080001"},
    )

    assert profile == "costImpactMaterials"


def test_infer_profile_name_falls_back_to_detect():
    profile = ChatPresentationTableProfileInferenceService.infer_profile_name(
        path="/products/90261255/stock",
        entity=None,
        sample_row={
            "branch": "01",
            "warehouse": "01",
            "current_quantity": 10,
        },
    )

    assert profile in {"stockProductPositions", "stock"}
