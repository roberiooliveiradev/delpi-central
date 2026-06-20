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
    assert patterns.get("codeToken")
    assert patterns.get("primaryDrawingCode")
    assert ChatAssistantContentService.list("drawing_stamp", "patternLists", "length")
    assert ChatAssistantContentService.get_node("drawing_stamp", "productCodeResolution")


def test_drawing_stamp_detail_ocr_config():
    detail = ChatAssistantContentService.get_node("drawing_stamp", "detailOcr") or {}

    assert "stamp" in (detail.get("enabledRegions") or [])
    assert "bom" in (detail.get("enabledRegions") or [])
    assert float(detail.get("zoomMultiplier") or 0) >= 2.0
    assert isinstance(detail.get("subRegions"), dict)
    assert detail.get("subRegions", {}).get("stamp")
    assert detail.get("subRegions", {}).get("bom")
    preprocess = detail.get("preprocess") or {}
    assert preprocess.get("binarize") is True


def test_drawing_stamp_bom_candidate_bboxes():
    candidates = ChatAssistantContentService.get_node("drawing_stamp", "bomCandidateBboxes") or []

    assert len(candidates) >= 2
    assert all(isinstance(item, dict) and len(item.get("bbox") or []) == 4 for item in candidates)


def test_drawing_stamp_extraction_quality_retry_profiles():
    retry = ChatAssistantContentService.get_node("drawing_stamp", "extractionQualityRetry") or {}

    assert retry.get("enabled") is True
    assert int(retry.get("maxAttempts") or 0) >= 5

    attempts = retry.get("attempts") or []

    assert len(attempts) >= 5
    assert attempts[0].get("id") == "standard"
    assert attempts[-1].get("regionOcrEngines") == ["tesseract", "easyocr"]
