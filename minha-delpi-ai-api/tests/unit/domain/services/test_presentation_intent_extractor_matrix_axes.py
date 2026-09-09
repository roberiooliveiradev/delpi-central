"""PresentationIntentExtractor — eixos matrix curtos (heatmap)."""

from app.domain.services.presentation_intent_extractor_service import (
    PresentationIntentExtractorService,
)


def test_paren_product_warehouse_axes_are_short():
    intent = PresentationIntentExtractorService.extract(
        "Agora coloque isso em um gráfico de mapa de calor "
        "(produto × depósito/filial) em tons de azul."
    )
    assert intent.mark == "heatmap"
    assert intent.palette_family == "sequential-blue"
    joined = " ".join(intent.dimension_concepts).lower()
    assert "agora coloque" not in joined
    assert any("produto" in c for c in intent.dimension_concepts)
    assert any(
        "depósito" in c or "deposito" in c or "filial" in c
        for c in intent.dimension_concepts
    )


def test_sibling_machine_shift_matrix():
    intent = PresentationIntentExtractorService.extract(
        "heatmap máquina × turno pela produção"
    )
    assert intent.mark == "heatmap"
    assert any("máquina" in c or "maquina" in c for c in intent.dimension_concepts)
    assert any("turno" in c for c in intent.dimension_concepts)


def test_sibling_branch_warehouse_matrix():
    intent = PresentationIntentExtractorService.extract("filial × armazém")
    assert len(intent.dimension_concepts) >= 2
    assert any("filial" in c for c in intent.dimension_concepts)
    assert any("armazém" in c or "armazem" in c for c in intent.dimension_concepts)


def test_negative_without_matrix_does_not_invent_dims():
    intent = PresentationIntentExtractorService.extract(
        "mostre em mapa de calor em tons de azul"
    )
    assert intent.mark == "heatmap"
    assert intent.dimension_concepts == ()


def test_negative_slash_unit_is_not_two_matrix_axes():
    """kg/h no texto livre não deve virar dois dimensionConcepts via split global."""
    intent = PresentationIntentExtractorService.extract(
        "mostre a vazão em kg/h na tabela"
    )
    assert intent.mark is None or intent.mark != "heatmap"
    assert intent.dimension_concepts == ()
