"""Padrões e regras de validação carregados dos bundles assistant."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService

configure_domain_infrastructure_ports()


def test_drawing_stamp_patterns_compile():
    assert ChatDrawingPatternsService.component_code().search("10091640")
    assert ChatDrawingPatternsService.intermediate_code().search("50215434")
    assert ChatDrawingPatternsService.revision().search("REV.02")
    assert ChatDrawingPatternsService.bom_section().search("LISTA DE MATERIAIS")


def test_drawing_validation_rules_from_json():
    assert ChatDrawingPatternsService.length_tolerance_ratio() == 0.05
    assert ChatDrawingPatternsService.decape_tolerance_mm() == 1.0
    assert ChatDrawingPatternsService.max_segment_length_checks() == 6
    assert ChatDrawingPatternsService.final_inspection_work_center_prefix() == "CT-99"


def test_intermediate_segment_pattern_parses_description():
    match = ChatDrawingPatternsService.intermediate_segment().search(
        "CT26VERM-00036/04/06-0000-0000"
    )

    assert match
    assert match.group(1) == "00036"
    assert match.group(2) == "04"
    assert match.group(3) == "06"


def test_stamp_extraction_patterns_from_json():
    assert ChatDrawingPatternsService.code_token().search("90260140")
    assert ChatDrawingPatternsService.primary_drawing_code().match("90260140")
    assert ChatDrawingPatternsService.filename_code().match("90260140-1")
    assert ChatDrawingPatternsService.high_confidence_threshold() == 0.85
