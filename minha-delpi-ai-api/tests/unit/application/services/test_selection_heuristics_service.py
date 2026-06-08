from app.application.services.external_actions.external_action_selection_heuristics_service import (
    ExternalActionSelectionHeuristicsService,
)


def test_looks_like_product_question_matches_estoque():
    assert ExternalActionSelectionHeuristicsService.looks_like_product_question(
        "qual o estoque do produto 10080022"
    )


def test_looks_like_lmp_question_excludes_transforma():
    assert not ExternalActionSelectionHeuristicsService.looks_like_lmp_question(
        "resumo do transforma mais"
    )


def test_looks_like_lmp_question_matches_lmp_term():
    assert ExternalActionSelectionHeuristicsService.looks_like_lmp_question(
        "liste as lmps da ov 12345",
        extract_sale_number=lambda value: "12345" if "12345" in str(value) else None,
    )
