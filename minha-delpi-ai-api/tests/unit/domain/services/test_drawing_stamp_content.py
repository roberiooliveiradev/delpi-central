"""Conteúdo JSON — OCR hierárquico carimbo (Onda 14)."""

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


def test_drawing_stamp_bundle_has_core_sections():
    assert ChatAssistantContentService.list("drawing_stamp", "stampFieldLabels", "productCode")
    assert ChatAssistantContentService.list("drawing_stamp", "titlePatterns", "chicotePrefixes")
    assert ChatAssistantContentService.list("drawing_stamp", "customerExclusionPrefixes")
    assert ChatAssistantContentService.get_node("drawing_stamp", "regionBboxes", "stamp")


def test_drawing_stamp_clarifications_from_json():
    unresolved = ChatAssistantContentService.get(
        "drawing_stamp",
        "clarifications",
        "unresolvedProductCode",
    )

    assert unresolved
    assert "90260140" in unresolved


def test_drawing_stamp_conflict_types_registered():
    conflicts = ChatAssistantContentService.get_node("drawing_stamp", "conflictTypes") or {}

    assert "stamp_vs_message" in conflicts
    assert "bom_code_promoted" in conflicts


def test_drawing_stamp_native_gate_markers():
    markers = ChatAssistantContentService.list("drawing_stamp", "nativeTextGate", "stampMarkers")
    gate = ChatAssistantContentService.get_node("drawing_stamp", "nativeTextGate") or {}

    assert "CÓDIGO DELPI" in markers or "CODIGO DELPI" in markers
    assert int(gate.get("minMarkerHits") or 0) >= 1


def test_drawing_stamp_patterns_section_exists():
    patterns = ChatAssistantContentService.get_node("drawing_stamp", "patterns") or {}

    assert patterns.get("componentCode")
    assert ChatAssistantContentService.list("drawing_stamp", "patternLists", "length")
