from app.domain.services.chat_operational_factual_verdict_content_service import (
    ChatOperationalFactualVerdictContentService,
)
from app.domain.services.chat_operational_factual_verdict_service import (
    ChatOperationalFactualVerdictService,
)
from app.domain.services.chat_presentation_prose_delivery_service import (
    ChatPresentationProseDeliveryService,
)


def test_content_service_loads_profile_fidelity_rule():
    rule = ChatOperationalFactualVerdictContentService.fidelity_rule("structure_exclusivity")

    assert "MP exclusiva" in rule
    assert "compartilhadas" in rule


def test_extract_scalar_from_kpi_metadata():
    metadata = {
        "path": "/products/90260882/structure/exclusivity",
        "kpiPresentation": {
            "cards": [
                {"label": "MPs exclusivas", "value": 0, "unit": "MP"},
            ],
        },
    }

    count = ChatOperationalFactualVerdictService.extract_scalar(
        metadata,
        "structure_exclusivity",
    )

    assert count == 0


def test_strip_contradictory_claims_when_scalar_zero():
    answer = (
        "O produto tem exclusividade definida por matérias-primas compartilhadas "
        "com outros PAs."
    )

    stripped = ChatOperationalFactualVerdictService.strip_contradictory_claims(
        answer,
        "structure_exclusivity",
        0,
    )

    assert stripped == ""


def test_preserve_template_markdown_when_profile_requests_it():
    metadata = {
        "path": "/products/90260882/structure/exclusivity",
        "apiDelpiResponseMeta": {"entity": "product_structure_exclusivity"},
    }
    markdown = "**Resposta:** Não — nenhuma MP exclusiva."

    assert ChatPresentationProseDeliveryService.should_preserve_template_markdown_over_data_answer(
        markdown,
        metadata,
    )


def test_resolve_profile_key_from_presentation_profile():
    profile_key = ChatOperationalFactualVerdictService.resolve_profile_key(
        path="/products/90260882/structure/exclusivity",
        metadata={"apiDelpiResponseMeta": {"entity": "product_structure_exclusivity"}},
    )

    assert profile_key == "structure_exclusivity"
