from app.domain.services.gpt_instructions_adaptation_service import (
    GptInstructionsAdaptationService,
)


def test_adapts_obsolete_product_search_path():
    raw = "GET /products/search/description?description=terminal"
    adapted = GptInstructionsAdaptationService.adapt(raw, source_name="product_api_instructions.md")

    assert "/products/search/description" not in adapted
    assert "/products/search?description=" in adapted


def test_adapts_product_singular_paths():
    raw = "Consulta `/product/10080522/structure` conforme guia."
    adapted = GptInstructionsAdaptationService.adapt(raw, source_name="GPT_instructions.md")

    assert "/product/" not in adapted
    assert "/products/10080522/structure" in adapted


def test_output_filename_slug():
    name = GptInstructionsAdaptationService.output_filename(
        "Understanding DELPI Intermediate Product Codes.md"
    )
    assert name.startswith("gpt-")
    assert name.endswith(".md")
