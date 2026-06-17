from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_detection_service import (
    ChatProductQueryIntentDetectionService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
)


def test_detect_pipeline_loaded_from_json():
    pipeline = ChatProductQueryIntentDetectionService._detect_pipeline()

    assert pipeline
    assert pipeline[0]["probe"] == "drawingAnalysis"
    assert pipeline[-1]["predicate"] == "descriptionQuestion"


def test_refine_pipeline_loaded_from_json():
    pipeline = ChatProductQueryIntentDetectionService._refinement_pipeline()

    assert pipeline
    assert pipeline[-1]["probe"] == "singleScopeIntent"


def test_detect_matches_legacy_service():
    message = "estoque do produto 90260142"

    assert (
        ChatProductQueryIntentDetectionService.detect(message)
        == ChatProductQueryIntent.STOCK
    )


def test_refine_matches_legacy_service():
    message = "estoque do produto 90260142"

    assert (
        ChatProductQueryIntentDetectionService.refine_operational_intent_from_full(message)
        == ChatProductQueryIntent.STOCK
    )


def test_detect_playbook_scope_before_stock_sub_intent():
    message = "status fabril do produto 90269002 hoje"

    assert (
        ChatProductQueryIntentDetectionService.detect(message)
        == ChatProductQueryIntent.FULL
    )


def test_single_scope_intent_from_json_map():
    message = "estrutura do produto 90260142"

    assert (
        ChatProductQueryIntentDetectionService.refine_operational_intent_from_full(message)
        == ChatProductQueryIntent.STRUCTURE
    )


def test_mixed_documental_operational_probe():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "explique a politica de estoque do produto"
    )

    assert ChatProductQueryIntentDetectionService.looks_like_mixed_documental_operational(
        normalized
    )
