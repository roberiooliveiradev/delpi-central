from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_format_refinement_intent_service import (
    ChatPresentationFormatRefinementIntentService,
)


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def test_loose_keyword_with_reference_detects_chart():
    intent = ChatPresentationFormatRefinementIntentService.resolve(
        "plote barras com os dados acima",
        has_prior_operation=True,
    )

    assert intent.is_refinement is True
    assert intent.requested_format == "chart"
    assert intent.source in {"loose", "vocabulary", "router"}


def test_ambiguous_refinement_without_format():
    intent = ChatPresentationFormatRefinementIntentService.resolve(
        "reformate de outro jeito o resultado anterior",
        has_prior_operation=True,
    )

    assert intent.is_refinement is True
    assert intent.requested_format is None
    assert intent.source == "ambiguous"


def test_dashboard_hint_with_context():
    intent = ChatPresentationFormatRefinementIntentService.resolve(
        "mostre em painel com os mesmos dados",
        has_prior_operation=True,
    )

    assert intent.is_refinement is True
    assert intent.requested_format == "dashboard"


def test_no_prior_operation_skips_loose_keywords():
    intent = ChatPresentationFormatRefinementIntentService.resolve(
        "mostre em gráfico",
        has_prior_operation=False,
    )

    assert intent.is_refinement is True
    assert intent.requested_format == "chart"
