from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def test_build_text_presentation_from_product_payload():
    presenter = ExternalActionResultPresenter()

    text = presenter.build_text_presentation(
        {
            "product": {
                "code": "10080055",
                "description": "TERM. FASTON 4,80X0,50",
                "type": "ME",
                "unit": "UN",
            }
        },
        path="/products/{code}",
    )

    assert text is not None
    assert text["type"] == "markdown"
    assert "10080055" in text["markdown"]
    assert "TERM. FASTON" in text["markdown"]
