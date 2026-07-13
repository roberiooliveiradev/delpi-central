"""Classificação PI/MP/consumível no pipeline de desenho (vocabulário técnico)."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_bom_reference_noise_service import (
    ChatDrawingBomReferenceNoiseService,
)
from app.domain.services.chat_drawing_intermediate_code_service import (
    ChatDrawingIntermediateCodeService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_product_family_classification_service import (
    ChatDrawingProductFamilyClassificationService as Family,
)
from app.domain.services.chat_technical_description_vocabulary_service import (
    ChatTechnicalDescriptionVocabularyService,
)

configure_domain_infrastructure_ports()


def test_classify_intermediate_with_signature():
    family = Family.classify(
        "50232222",
        description="CB1,50VERD-00255/06/06-6314-0111",
    )

    assert family.kind == Family.KIND_INTERMEDIATE
    assert family.group_code == "5023"


def test_classify_raw_material_terminal_group():
    family = Family.classify("10080063")

    assert family.kind == Family.KIND_RAW_MATERIAL
    assert family.group_code == "1008"
    assert family.label == "terminais"


def test_classify_consumable_termoencolhivel_group():
    family = Family.classify("10130001")

    assert family.kind == Family.KIND_CONSUMABLE
    assert family.group_code == "1013"


def test_false_intermediate_termoencolhivel_via_vocabulary_bridge():
    row = {
        "code": "50250279",
        "description": "LUVATERMOENCOLHVEL =",
    }

    assert Family.is_false_intermediate_candidate(
        row["code"],
        description=row["description"],
    )
    assert ChatDrawingBomReferenceNoiseService.is_false_intermediate_bom_row(row)


def test_intermediate_signature_accepts_ca_and_four_letter_color():
    assert Family.has_intermediate_signature("CA0,75PRET-00120/06/06-0000-0000")
    assert Family.extract_intermediate_color("CA0,75PRET-00120") == "PRET"
    assert Family.extract_intermediate_color("CB1,50VERD-00255") == "VERD"


def test_vocabulary_soft_signature_without_full_segment():
    # Isolação + cor 4 letras, mesmo sem decape completo no regex stamp.
    assert Family.has_intermediate_signature("CABO CB1,50 VERD 255MM")


def test_intermediate_code_collect_skips_false_bom_row():
    codes = ChatDrawingIntermediateCodeService.collect_codes(
        full_text="",
        bom_rows=[
            {
                "code": "50250279",
                "description": "TERMOENCOLHIVEL 6MM",
            },
            {
                "code": "50232222",
                "description": "CB1,50VERD-00255/06/06-6314-0111",
            },
        ],
        bom_sources=[("bom", "50232222\n50250279")],
        product_code="90260001",
    )

    assert "50232222" in codes
    assert "50250279" not in codes


def test_color_ocr_markers_include_vocabulary_insulation():
    markers = ChatDrawingPatternsService.intermediate_color_ocr_markers("AZUL")

    assert "CB20AZUL" in markers
    assert "CA20AZUL" in markers
    assert "CT20AZUL" in markers


def test_color_signature_pattern_accepts_all_insulation_codes():
    match = ChatDrawingPatternsService.compile_validation(
        "intermediateColorSignature"
    ).match("CA18AZUL")

    assert match
    assert match.group(1) == "AZUL"

    match_ct = Family.intermediate_color_signature_pattern().match("CT26VERM")
    assert match_ct
    assert match_ct.group(1) == "VERM"


def test_vocabulary_exposes_consumable_and_four_letter_colors():
    assert "1013" in ChatTechnicalDescriptionVocabularyService.consumable_group_codes()
    assert "PRET" in ChatTechnicalDescriptionVocabularyService.intermediate_four_letter_colors()
    assert "1008" in ChatTechnicalDescriptionVocabularyService.material_group_code_prefixes()
