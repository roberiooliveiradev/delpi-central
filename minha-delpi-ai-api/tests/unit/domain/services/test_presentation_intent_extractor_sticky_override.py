"""PresentationIntentExtractor — mark explícito vs sticky session format."""

from app.domain.services.presentation_intent_extractor_service import (
    PresentationIntentExtractorService,
)


def test_heatmap_message_outranks_sticky_table_session_format():
    intent = PresentationIntentExtractorService.extract(
        "Agora coloque isso em um gráfico de mapa de calor.",
        requested_presentation="table",
    )
    assert intent.mark == "heatmap"
    assert intent.view == "chart"


def test_sibling_line_chart_outranks_sticky_table():
    intent = PresentationIntentExtractorService.extract(
        "mostre em gráfico de linha",
        requested_presentation="table",
    )
    assert intent.mark == "line"
    assert intent.view == "chart"


def test_negative_table_request_without_chart_mark_keeps_table():
    intent = PresentationIntentExtractorService.extract(
        "quero ver em tabela",
        requested_presentation="table",
    )
    assert intent.mark is None
    assert intent.view in {"table", None} or intent.view == "table"
